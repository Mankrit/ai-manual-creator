import os
import json
import shutil
import re
import subprocess
import argparse

def create_title_slide(title_text, subtitle_text, output_path):
    """
    Generates a premium obsidian-dark title/conclusion slide image.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Warning: Pillow is not available. Skipping title slide creation.")
        return False
        
    width, height = 1280, 800
    # Obsidian-dark background #0f1125
    img = Image.new("RGBA", (width, height), (15, 17, 37, 255))
    draw = ImageDraw.Draw(img)
    
    # Premium subtle glowing spots
    draw.ellipse([(-200, -200), (400, 400)], fill=(79, 70, 229, 25))  # Indigo
    draw.ellipse([(900, 400), (1500, 1000)], fill=(219, 39, 119, 20)) # Pink
    
    try:
        title_font = ImageFont.load_default(size=44)
        subtitle_font = ImageFont.load_default(size=20)
    except Exception:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        
    # Draw title
    draw.text((width / 2, height / 2 - 40), title_text, fill=(255, 255, 255, 255), anchor="mm", font=title_font)
    
    # Draw subtitle
    if subtitle_text:
        draw.text((width / 2, height / 2 + 40), subtitle_text, fill=(156, 163, 175, 255), anchor="mm", font=subtitle_font)
        
    img.convert("RGB").save(output_path, "PNG")
    return True

def extract_walkthrough_steps(content):
    """
    Parses the Markdown content and extracts user guide steps that contain screenshots.
    Returns a list of dicts: [{'text': '...', 'image': '...'}]
    """
    steps = []
    
    # Locate the User Guide section (typically starting with '## 1' and ending before '## 2')
    user_guide_match = re.search(r"##\s+1\b.*?(?=##\s+2\b|$)", content, re.DOTALL)
    if not user_guide_match:
        return steps
        
    user_guide_content = user_guide_match.group(0)
    
    # Match all image links in the User Guide, e.g. ![caption](image.png)
    matches = re.finditer(r"!\[(.*?)\]\((.*?)\)", user_guide_content)
    for m in matches:
        caption = m.group(1).strip()
        image_name = m.group(2).strip()
        
        # Clean up caption for TTS (remove bold, stars, backticks, links)
        clean_text = re.sub(r"[`\*\_\~]", "", caption)
        clean_text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean_text)
        clean_text = clean_text.strip()
        
        if clean_text and image_name:
            if image_name.lower().endswith(('.png', '.jpg', '.jpeg')):
                steps.append({
                    "text": clean_text,
                    "image": image_name
                })
                
    return steps

def generate_narration_script(module_name, steps, model_name, lang="en"):
    """
    Calls the LLM to write a professional tutorial voice-over script for each step in the target language.
    Returns a list of dicts: [{'narration': '...', 'pause_after': 1.5}]
    """
    import litellm
    from dotenv import load_dotenv
    load_dotenv()
    
    steps_input = []
    for idx, step in enumerate(steps):
        steps_input.append({
            "slide_index": idx,
            "original_caption": step["text"],
            "image": step["image"]
        })
        
    prompt = f"""You are a professional video narrator script writer for software tutorials.
Your goal is to convert raw screenshot captions and slide metadata into an engaging, natural, and friendly spoken script in the language: "{lang}" (standard Hindi in Devanagari script for "hi", Hinglish using English alphabet for "hinglish", or English for "en") for a video tutorial walkthrough of the module: "{module_name}".

Here are the slide details in chronological order:
{json.dumps(steps_input, indent=2)}

Please write the narration voice-over script and slide hold pacing timings.
Requirements:
1. Slide 0 is the Intro slide. Write a friendly introduction greeting the user and summarizing what this tutorial will demonstrate.
2. Slide {len(steps) - 1} is the Outro slide. Write a professional concluding remark. Do NOT ask the viewer to like, share, subscribe, comment, or perform other common YouTube-style call-to-actions, This is a manual tutorial video.
3. For all other screenshot slides, write a natural voice-over instructing the user on what action to take (e.g. "Next, select Dark Mode from the theme dropdown selection."). Avoid technical descriptions like "this screenshot shows...". Speak in the second person ("you" / "we").
4. Specify a pacing hold `pause_after` (in seconds) for how long the slide should linger static after the voice narration finishes. Set it to 0.4 to 0.8 seconds to keep the tutorial well-paced, engaging, and snappy.

Write the script output narration sentences ENTIRELY in the target language: "{lang}". If the language is "hi", output in Devanagari script. If the language is "hinglish", use Latin script (English alphabet) but mix Hindi/English as naturally spoken in India.

You MUST respond ONLY with a valid JSON array of objects, with each object containing exactly:
- "narration": The spoken voice-over script text (string)
- "pause_after": The hold duration in seconds after speech finishes (float)

Response JSON format:
[
  {{
    "narration": "Welcome to the...",
    "pause_after": 0.5
  }}
]
"""
    try:
        # Call LLM
        response = litellm.completion(
            model=model_name,
            messages=[
                {"role": "system", "content": f"You are a professional video tutorial script generator for language '{lang}'. Respond ONLY with a valid JSON array of objects. Do not include markdown codeblocks or other explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4096
        )
        
        resp_msg = response.choices[0].message.content
        raw_content = resp_msg.strip() if resp_msg else ""
        
        # Robust JSON array extraction
        start = raw_content.find('[')
        end = raw_content.rfind(']')
        if start != -1 and end != -1 and end > start:
            clean_json_str = raw_content[start:end+1]
        else:
            clean_json_str = re.sub(r"^```json\s*", "", raw_content)
            clean_json_str = re.sub(r"\s*```$", "", clean_json_str)
            
        # Repair trailing commas in JSON (a common LLM formatting error)
        clean_json_str = re.sub(r',\s*\]', ']', clean_json_str)
        clean_json_str = re.sub(r',\s*\}', '}', clean_json_str)
        
        try:
            script = json.loads(clean_json_str)
        except json.JSONDecodeError:
            repaired_json = clean_json_str.strip()
            # Count open vs close braces
            open_braces = repaired_json.count('{')
            close_braces = repaired_json.count('}')
            if open_braces > close_braces:
                # Add closing quote if unclosed
                unescaped_quotes = len(re.findall(r'(?<!\\)"', repaired_json))
                if unescaped_quotes % 2 != 0:
                    repaired_json += '"'
                if not repaired_json.endswith('}'):
                    if repaired_json.endswith(','):
                        repaired_json = repaired_json[:-1]
                    repaired_json += '}'
            if not repaired_json.endswith(']'):
                if repaired_json.endswith(','):
                    repaired_json = repaired_json[:-1]
                repaired_json += ']'
            script = json.loads(repaired_json)
            
        print(f"  LLM successfully generated voice-over narrator script in '{lang}'.")
        return script
    except Exception as e:
        print(f"  Error generating narration script in '{lang}': {e}")
        # Fallback to captions
        fallback_script = []
        for idx, step in enumerate(steps):
            fallback_text = step["text"]
            if idx == 0:
                fallback_text = "Welcome to the tutorial." if lang != "hi" else "ट्यूटोरियल में आपका स्वागत है।"
            elif idx == len(steps) - 1:
                fallback_text = "Thank you for watching." if lang != "hi" else "देखने के लिए धन्यवाद।"
            fallback_script.append({
                "narration": fallback_text,
                "pause_after": 1.5
            })
        return fallback_script

def translate_chunk(chunk, lang, model_name):
    """
    Translates a single chunk of markdown text.
    """
    import litellm
    from dotenv import load_dotenv
    load_dotenv()
    
    prompt = f"""You are a professional technical translator.
Your goal is to translate the following markdown documentation section into the target language: "{lang}".
- If the target language is "hi", translate to standard, professional Hindi.
- If the target language is "hinglish", translate to natural Hinglish (using Latin script, i.e., English letters, but mixing Hindi/English vocabulary).

Requirements:
1. Keep the exact same Markdown syntax, headings, lists, bold text, code tags, and HTML tags.
2. DO NOT change or translate any code blocks, class names, file paths, selectors, variable names, or technical commands.
3. Keep all image link filenames exactly the same (e.g., keep `![Caption](image.png)` intact, but you may translate the Caption text).
4. Output ONLY the translated text. Do not include any introductory notes, explanations, or enclosing backticks.

Markdown text to translate:
{chunk}
"""
    try:
        response = litellm.completion(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a professional technical translator. Output ONLY the translation. Do not write explanations or markdown wrapping block ticks around the whole text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=4096
        )
        translated = response.choices[0].message.content.strip()
        if translated.startswith("```markdown") and translated.endswith("```"):
            translated = translated[11:-3].strip()
        elif translated.startswith("```") and translated.endswith("```"):
            translated = translated[3:-3].strip()
        return translated
    except Exception as e:
        print(f"    Error translating chunk: {e}")
        return chunk


def translate_markdown(content, lang, model_name):
    """
    Translates the markdown documentation text to the target language by splitting
    it into header-based chunks to prevent LLM translation bypass.
    """
    if lang == "en":
        return content
        
    print(f"    Splitting markdown into sections for '{lang}' translation...")
    
    # Split by markdown headers (# to ####) while keeping the headers in the split output
    pattern = r"(^(?:#{1,4})\s+.*$)"
    parts = re.split(pattern, content, flags=re.MULTILINE)
    
    translated_parts = []
    for part in parts:
        part_str = part.strip()
        if not part_str:
            continue
            
        # If it's a header line
        if part_str.startswith("#"):
            translated_header = translate_chunk(part_str, lang, model_name)
            translated_parts.append(translated_header)
        else:
            # If it's pure code block or very small, skip translation to save tokens
            if len(part_str) < 10 or (part_str.startswith("```") and part_str.endswith("```")):
                translated_parts.append(part)
            else:
                translated_section = translate_chunk(part, lang, model_name)
                translated_parts.append(translated_section)
                
    return "\n\n".join(translated_parts)

def get_localized_slide_text(title, lang):
    """
    Returns the title and subtitle strings for slide cards based on target language.
    Always returns English text to prevent Pillow font support issues with non-ASCII scripts.
    """
    return {
        "intro_title": f"{title} Walkthrough",
        "intro_subtitle": "Video Tutorial Guide",
        "outro_title": "Walkthrough Completed",
        "outro_subtitle": "Thank You for Watching"
    }


def generate_video(module_path, steps, output_video_path, script, tts_engine="edge-tts", voice="en-US-AndrewNeural", pacing_scale_factor=0.35):
    """
    Generates a voice-over walkthrough video using edge-tts and moviepy, paced by LLM script.
    """
    try:
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
        if not hasattr(ImageClip, "with_duration"):
            ImageClip.with_duration = ImageClip.set_duration
            ImageClip.with_audio = ImageClip.set_audio
    except ImportError:
        print("Warning: moviepy is not installed or available in this environment. Skipping video generation.")
        return False
        
    temp_audios = []
    temp_clips = []
    temp_audio_clips = []
    
    print(f"  Rendering video tutorial walkthrough ({len(steps)} slides)...")
    
    try:
        for idx, step in enumerate(steps):
            image_name = step["image"]
            image_path = os.path.join(module_path, image_name)
            
            if not os.path.exists(image_path):
                print(f"    Warning: slide screenshot {image_name} not found, skipping step.")
                continue
                
            script_item = script[idx] if idx < len(script) else {"narration": step["text"], "pause_after": 1.5}
            text = script_item.get("narration", step["text"])
            
            # Apply scaling factor to pause gap
            raw_pause = script_item.get("pause_after", 1.5)
            pause_after = raw_pause * pacing_scale_factor
            
            audio_name = f"__temp_step_{idx}.mp3"
            audio_path = os.path.join(module_path, audio_name)
            
            # Generate TTS audio
            cmd = ["edge-tts", "--text", text, "--write-media", audio_path, "--voice", voice]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            temp_audios.append(audio_path)
            
            audio_clip = AudioFileClip(audio_path)
            temp_audio_clips.append(audio_clip)
            
            # Duration is audio duration + scaled pause pacing
            slide_duration = audio_clip.duration + pause_after
            
            image_clip = ImageClip(image_path).with_duration(slide_duration)
            slide_with_audio = image_clip.with_audio(audio_clip)
            temp_clips.append(slide_with_audio)
            
        if temp_clips:
            final_video = concatenate_videoclips(temp_clips, method="compose")
            
            # Unique temp audio file in the module directory to avoid file locks and workspace collisions
            temp_audio_file_path = os.path.join(module_path, "__temp_audio_final.m4a")
            
            final_video.write_videofile(
                output_video_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac",
                temp_audiofile=temp_audio_file_path,
                remove_temp=True,
                logger=None
            )
            
            # Release all file handles before finishing
            try:
                final_video.close()
            except Exception:
                pass
                
            for clip in temp_clips:
                try:
                    if hasattr(clip, "audio") and clip.audio:
                        clip.audio.close()
                    clip.close()
                except Exception:
                    pass
                    
            for a_clip in temp_audio_clips:
                try:
                    a_clip.close()
                except Exception:
                    pass
                
            print(f"    Walkthrough video successfully saved to {output_video_path}")
            return True
        else:
            print("    No clips compiled.")
            return False
            
    except Exception as e:
        print(f"    Error compiling tutorial video: {str(e)}")
        return False
    finally:
        # Extra safety check: close anything we missed in case of error
        for clip in temp_clips:
            try:
                if hasattr(clip, "audio") and clip.audio:
                    clip.audio.close()
                clip.close()
            except Exception:
                pass
        for a_clip in temp_audio_clips:
            try:
                a_clip.close()
            except Exception:
                pass
                
        # Clean up temporary audio files
        for audio_path in temp_audios:
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass

def compile_docs(config_path="config.json"):
    output_dir = "output"
    
    # Load config settings
    if not os.path.exists(config_path):
        print(f"Config file '{config_path}' not found. Defaulting to standard settings.")
        config = {}
    else:
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error reading config {config_path}: {e}")
            config = {}
            
    models = config.get("models", {})
    # Use script_narrator model if defined, fallback to writer
    narrator_model = models.get("script_narrator", models.get("writer", "openai/cohere/north-mini-code:free"))
    translator_model = models.get("translator", models.get("writer", "openai/cohere/north-mini-code:free"))
    
    video_cfg = config.get("walkthrough_video", {})
    tts_engine = video_cfg.get("tts_engine", "edge-tts")
    default_voice = video_cfg.get("voice", "en-US-AndrewNeural")
    pacing_scale_factor = video_cfg.get("pacing_scale_factor", 0.35)
    
    loc_cfg = config.get("localization", {})
    languages = loc_cfg.get("languages", ["en"])
    voices = loc_cfg.get("voices", {})
    
    portal_docs_dir = os.path.join("portal", "public", "docs")
    
    if os.path.exists(portal_docs_dir):
        try:
            shutil.rmtree(portal_docs_dir)
        except Exception as e:
            print(f"Warning: could not clean docs directory: {e}")
            
    os.makedirs(portal_docs_dir, exist_ok=True)
    
    catalog = []
    
    if not os.path.exists(output_dir):
        print(f"Output directory '{output_dir}' does not exist.")
        return
        
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path):
            module_key = item
            # Avoid loading generated localized manuals as raw modules
            md_files = [f for f in os.listdir(item_path) if f.lower().endswith(".md") and not any(f.lower().endswith(f"_{l}.md") for l in languages if l != "en")]
            if not md_files:
                continue
                
            dest_module_dir = os.path.join(portal_docs_dir, module_key)
            os.makedirs(dest_module_dir, exist_ok=True)
            
            # Copy baseline screenshots/resources (exclude md and walkthrough files, they copy per-language)
            for f in os.listdir(item_path):
                if f.startswith("__temp_") or f.lower().endswith(".md") or "walkthrough" in f:
                    continue
                src_file = os.path.join(item_path, f)
                dest_file = os.path.join(dest_module_dir, f)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dest_file)
                
            primary_md = md_files[0]
            primary_md_path = os.path.join(item_path, primary_md)
            
            # Read master English manual
            content_en = ""
            title_en = module_key.replace("_", " ").title()
            try:
                with open(primary_md_path, "r", encoding="utf-8") as f:
                    content_en = f.read()
                    match = re.search(r"^#\s+(.+)$", content_en, re.MULTILINE)
                    if match:
                        title_en = match.group(1).replace("MODULE:", "").strip()
            except Exception as e:
                print(f"Error reading {primary_md_path}: {e}")
            
            compiled_languages = []
            video_files = {}
            
            # Loop over all configured target languages
            for lang in languages:
                print(f"  Processing language '{lang}' for module '{module_key}'...")
                
                if lang == "en":
                    md_filename = primary_md
                    video_filename = "walkthrough.mp4"
                    content_lang = content_en
                    title_lang = title_en
                else:
                    md_filename = f"{module_key}_{lang}.md"
                    video_filename = f"walkthrough_{lang}.mp4"
                    lang_md_path = os.path.join(item_path, md_filename)
                    
                    # Generate translated manual if missing
                    if not os.path.exists(lang_md_path):
                        print(f"    Translating manual content into '{lang}'...")
                        content_lang = translate_markdown(content_en, lang, translator_model)
                        with open(lang_md_path, "w", encoding="utf-8") as f:
                            f.write(content_lang)
                    else:
                        with open(lang_md_path, "r", encoding="utf-8") as f:
                            content_lang = f.read()
                            
                    # Extract translated title
                    title_lang = title_en
                    match = re.search(r"^#\s+(.+)$", content_lang, re.MULTILINE)
                    if match:
                        title_lang = match.group(1).replace("MODULE:", "").strip()
                
                # Copy localized markdown manual to portal
                lang_dest_md_path = os.path.join(dest_module_dir, md_filename)
                with open(os.path.join(item_path, md_filename), "w", encoding="utf-8") as f:
                    f.write(content_lang)
                shutil.copy2(os.path.join(item_path, md_filename), lang_dest_md_path)
                
                # Build localized video
                output_video_path = os.path.join(item_path, video_filename)
                script_filename = video_filename.replace(".mp4", "_script.json")
                script_path = os.path.join(item_path, script_filename)
                
                raw_steps = extract_walkthrough_steps(content_lang)
                has_video = False
                
                if raw_steps:
                    # Check if walkthrough steps/screenshots have changed compared to the saved script
                    if os.path.exists(script_path):
                        try:
                            with open(script_path, "r", encoding="utf-8") as sf:
                                saved_script = json.load(sf)
                            
                            steps_changed = False
                            if len(saved_script) != len(raw_steps) + 2:
                                steps_changed = True
                            else:
                                for idx, raw_step in enumerate(raw_steps):
                                    script_img = saved_script[idx + 1].get("image")
                                    if script_img != raw_step["image"]:
                                        steps_changed = True
                                        break
                                        
                            if steps_changed:
                                print(f"    Notice: Walkthrough steps or screenshots changed in the manual for '{lang}'. Invalidating cache to trigger regeneration.")
                                if os.path.exists(output_video_path):
                                    os.remove(output_video_path)
                                os.remove(script_path)
                        except Exception as e:
                            print(f"    Warning: failed to read or validate walkthrough script '{script_filename}': {e}")
                            
                    if not os.path.exists(output_video_path):
                        print(f"    Generating walkthrough video for language '{lang}'...")
                        
                        # 1. Create localized title card images
                        intro_img_name = f"__temp_intro_{lang}.png"
                        outro_img_name = f"__temp_outro_{lang}.png"
                        intro_path = os.path.join(item_path, intro_img_name)
                        outro_path = os.path.join(item_path, outro_img_name)
                        
                        slide_txt = get_localized_slide_text(title_en, lang)
                        create_title_slide(slide_txt["intro_title"], slide_txt["intro_subtitle"], intro_path)
                        create_title_slide(slide_txt["outro_title"], slide_txt["outro_subtitle"], outro_path)
                        
                        # Assemble full localized slide deck
                        steps = [{"text": slide_txt["intro_title"], "image": intro_img_name}]
                        steps.extend(raw_steps)
                        steps.append({"text": slide_txt["outro_title"], "image": outro_img_name})
                        
                        # 2. Load existing script JSON if it exists, otherwise generate using LLM
                        script = None
                        if os.path.exists(script_path):
                            try:
                                with open(script_path, "r", encoding="utf-8") as sf:
                                    script = json.load(sf)
                                print(f"    Loaded existing walkthrough script from '{script_filename}'")
                            except Exception as e:
                                print(f"    Warning: failed to read walkthrough script '{script_filename}': {e}")
                                
                        if not script:
                            script = generate_narration_script(title_lang, steps, narrator_model, lang)
                            try:
                                with open(script_path, "w", encoding="utf-8") as sf:
                                    json.dump(script, sf, indent=2, ensure_ascii=False)
                                print(f"    Saved generated walkthrough script to '{script_filename}'")
                            except Exception as e:
                                print(f"    Warning: failed to save walkthrough script '{script_filename}': {e}")
                        
                        # 3. Compile the actual video
                        voice = voices.get(lang, default_voice)
                        generate_video(item_path, steps, output_video_path, script, tts_engine, voice, pacing_scale_factor)
                        
                        # Clean up localized temporary slides
                        for p in [intro_path, outro_path]:
                            if os.path.exists(p):
                                try:
                                    os.remove(p)
                                except Exception:
                                    pass
                    
                    # Copy compiled localized video and script to portal directory
                    if os.path.exists(output_video_path):
                        dest_video_path = os.path.join(dest_module_dir, video_filename)
                        shutil.copy2(output_video_path, dest_video_path)
                        has_video = True
                        
                        if os.path.exists(script_path):
                            dest_script_path = os.path.join(dest_module_dir, script_filename)
                            shutil.copy2(script_path, dest_script_path)
                        
                compiled_languages.append(lang)
                if has_video:
                    video_files[lang] = video_filename
            
            screenshots = [f for f in os.listdir(item_path) if f.endswith(".png") and not f.startswith("__temp_")]
            
            catalog_item = {
                "key": module_key,
                "title": title_en,
                "markdown_file": primary_md,
                "screenshots": screenshots,
                "languages": compiled_languages
            }
            if video_files:
                catalog_item["video"] = video_files
                
            catalog.append(catalog_item)
            
    # Save the catalog
    catalog_path = os.path.join(portal_docs_dir, "catalog.json")
    try:
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2)
        print(f"Compilation finished successfully. Saved catalog with {len(catalog)} modules to {catalog_path}")
    except Exception as e:
        print(f"Error writing catalog.json: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AI Manual Portal Compiler")
    parser.add_argument("--config", type=str, default="config.json", help="Path to config JSON file")
    args = parser.parse_args()
    compile_docs(args.config)
