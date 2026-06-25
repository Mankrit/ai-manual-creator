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
    
    # Locate the User Guide section (## 1. User Guide or similar)
    user_guide_match = re.search(r"##\s+1\.\s+User\s+Guide.*?(?=##\s+2\.\s+Technical|$)", content, re.DOTALL | re.IGNORECASE)
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

def generate_narration_script(module_name, steps, model_name):
    """
    Calls the LLM to write a professional tutorial voice-over script for each step.
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
Your goal is to convert raw screenshot captions and slide metadata into an engaging, natural, and friendly spoken script for a video tutorial walkthrough of the module: "{module_name}".

Here are the slide details in chronological order:
{json.dumps(steps_input, indent=2)}

Please write the narration voice-over script and slide hold pacing timings.
Requirements:
1. Slide 0 is the Intro slide. Write a friendly introduction greeting the user and summarizing what this tutorial will demonstrate.
2. Slide {len(steps) - 1} is the Outro slide. Write a professional concluding remark. Do NOT ask the viewer to like, share, subscribe, comment, or perform other common YouTube-style call-to-actions.
3. For all other screenshot slides, write a natural voice-over instructing the user on what action to take (e.g. "Next, select Dark Mode from the theme dropdown selection."). Avoid technical descriptions like "this screenshot shows...". Speak in the second person ("you" / "we").
4. Specify a pacing hold `pause_after` (in seconds) for how long the slide should linger static after the voice narration finishes. Set it to 0.4 to 0.8 seconds to keep the tutorial well-paced, engaging, and snappy.


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
                {"role": "system", "content": "You are a professional video tutorial script generator. Respond ONLY with a valid JSON array of objects. Do not include markdown codeblocks or other explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        raw_content = response.choices[0].message.content.strip()
        clean_json_str = re.sub(r"^```json\s*", "", raw_content)
        clean_json_str = re.sub(r"\s*```$", "", clean_json_str)
        
        script = json.loads(clean_json_str)
        print("  LLM successfully generated voice-over narrator script.")
        return script
    except Exception as e:
        print(f"  Error generating narration script: {e}")
        # Fallback to captions
        fallback_script = []
        for idx, step in enumerate(steps):
            fallback_script.append({
                "narration": step["text"] if idx > 0 and idx < len(steps)-1 else ("Welcome to the tutorial." if idx == 0 else "Thank you for watching."),
                "pause_after": 1.5
            })
        return fallback_script

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
    
    video_cfg = config.get("walkthrough_video", {})
    tts_engine = video_cfg.get("tts_engine", "edge-tts")
    voice = video_cfg.get("voice", "en-US-AndrewNeural")
    pacing_scale_factor = video_cfg.get("pacing_scale_factor", 0.35)

    
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
            md_files = [f for f in os.listdir(item_path) if f.endswith(".md")]
            if not md_files:
                continue
                
            dest_module_dir = os.path.join(portal_docs_dir, module_key)
            os.makedirs(dest_module_dir, exist_ok=True)
            
            # Copy all files
            for f in os.listdir(item_path):
                if f.startswith("__temp_"):
                    continue
                src_file = os.path.join(item_path, f)
                dest_file = os.path.join(dest_module_dir, f)
                if os.path.isfile(src_file):
                    shutil.copy2(src_file, dest_file)
                
            primary_md = md_files[0]
            primary_md_path = os.path.join(item_path, primary_md)
            
            title = module_key.replace("_", " ").title()
            content = ""
            try:
                with open(primary_md_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
                    if match:
                        title = match.group(1).replace("MODULE:", "").strip()
            except Exception as e:
                print(f"Error reading {primary_md_path}: {e}")
            
            has_video = False
            video_filename = "walkthrough.mp4"
            output_video_path = os.path.join(item_path, video_filename)
            
            # Parse user steps
            raw_steps = extract_walkthrough_steps(content)
            if raw_steps:
                if not os.path.exists(output_video_path):
                    print(f"Generating voice-over tutorial video for module '{module_key}'...")
                    
                    # 1. Create Intro & Outro title card images
                    intro_img_name = "__temp_intro.png"
                    outro_img_name = "__temp_outro.png"
                    intro_path = os.path.join(item_path, intro_img_name)
                    outro_path = os.path.join(item_path, outro_img_name)
                    
                    create_title_slide(f"{title} Walkthrough", "Video Tutorial Guide", intro_path)
                    create_title_slide("Walkthrough Completed", "Thank You for Watching", outro_path)
                    
                    # Assemble full step list
                    steps = [{"text": "Intro slide", "image": intro_img_name}]
                    steps.extend(raw_steps)
                    steps.append({"text": "Conclusion slide", "image": outro_img_name})
                    
                    # 2. Call LLM to generate narrative script with pacing pauses
                    script = generate_narration_script(title, steps, narrator_model)
                    
                    # 3. Compile the actual video
                    generate_video(item_path, steps, output_video_path, script, tts_engine, voice, pacing_scale_factor)

                    
                    # Clean up temporary slides
                    for p in [intro_path, outro_path]:
                        if os.path.exists(p):
                            try:
                                os.remove(p)
                            except Exception:
                                pass
                
                # Copy video file to portal directory
                if os.path.exists(output_video_path):
                    dest_video_path = os.path.join(dest_module_dir, video_filename)
                    shutil.copy2(output_video_path, dest_video_path)
                    has_video = True
            
            screenshots = [f for f in os.listdir(item_path) if f.endswith(".png") and not f.startswith("__temp_")]
            
            catalog_item = {
                "key": module_key,
                "title": title,
                "markdown_file": primary_md,
                "screenshots": screenshots
            }
            if has_video:
                catalog_item["video"] = video_filename
                
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
