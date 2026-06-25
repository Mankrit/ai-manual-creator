import { useState, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import { 
  BookOpen, 
  Terminal, 
  Eye, 
  Code, 
  Layers, 
  Search, 
  Copy, 
  Check, 
  ExternalLink, 
  Maximize2, 
  FileText, 
  X,
  Sparkles,
  ChevronRight,
  Video
} from 'lucide-react'

// Sub-component to handle copy-to-clipboard states
const CopyButton = ({ text }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button className="code-copy-btn" onClick={handleCopy} title="Copy code to clipboard">
      {copied ? <Check size={14} style={{ color: '#10b981' }} /> : <Copy size={14} />}
      <span>{copied ? "Copied!" : "Copy"}</span>
    </button>
  );
};

function App() {
  const [catalog, setCatalog] = useState([]);
  const [selectedModule, setSelectedModule] = useState(null);
  const [docContent, setDocContent] = useState('');
  const [activeTab, setActiveTab] = useState('user'); // 'user', 'technical', 'all'
  const [searchQuery, setSearchQuery] = useState('');
  const [lightboxImage, setLightboxImage] = useState(null);
  const [lightboxCaption, setLightboxCaption] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sessionVersion] = useState(() => Date.now());
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  // 1. Fetch Catalog on mount
  useEffect(() => {
    setLoading(true);
    fetch('/docs/catalog.json')
      .then(res => {
        if (!res.ok) {
          throw new Error('Failed to load docs catalog.');
        }
        return res.json();
      })
      .then(data => {
        setCatalog(data);
        if (data && data.length > 0) {
          setSelectedModule(data[0]);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // 2. Fetch Markdown file content when selectedModule or selectedLanguage changes
  useEffect(() => {
    if (!selectedModule) return;
    setDocContent('');
    
    const activeLanguage = (selectedModule.languages && selectedModule.languages.includes(selectedLanguage))
      ? selectedLanguage
      : 'en';
      
    const markdownFile = activeLanguage === 'en'
      ? selectedModule.markdown_file
      : `${selectedModule.key}_${activeLanguage}.md`;
      
    const filePath = `/docs/${selectedModule.key}/${markdownFile}`;
    fetch(filePath)
      .then(res => {
        if (!res.ok) {
          throw new Error(`Failed to load markdown content for ${selectedModule.title} (${activeLanguage})`);
        }
        return res.text();
      })
      .then(text => {
        setDocContent(text);
      })
      .catch(err => {
        console.error(err);
        setDocContent(`Error: Could not load guide content. (${err.message})`);
      });
  }, [selectedModule, selectedLanguage]);

  // 3. Filter catalog modules by search query
  const filteredCatalog = catalog.filter(module => 
    module.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    module.key.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // 4. Split Markdown into User Guide vs Technical Guide parts
  const splitMarkdown = (content) => {
    if (!content) return { user: '', tech: '', full: '' };

    const techIndex = content.search(/##\s+2\.\s+Technical/i);
    const userIndex = content.search(/##\s+1\.\s+User/i);

    let userPart = '';
    let techPart = '';

    if (techIndex !== -1) {
      techPart = content.slice(techIndex);
      if (userIndex !== -1) {
        userPart = content.slice(userIndex, techIndex);
      } else {
        userPart = content.slice(0, techIndex);
      }
    } else {
      userPart = content;
    }

    // Extract title if present at the top
    const titleMatch = content.match(/^#\s+.+$/m);
    const title = titleMatch ? titleMatch[0] + '\n\n' : '';

    return {
      user: userPart ? (userPart.startsWith('#') ? userPart : title + userPart) : content,
      tech: techPart ? (techPart.startsWith('#') ? techPart : title + techPart) : `${title}## Technical Guide\n\nNo developer documentation was generated for this module.`,
      full: content
    };
  };

  const docs = splitMarkdown(docContent);
  const activeContent = activeTab === 'user' ? docs.user : activeTab === 'technical' ? docs.tech : docs.full;

  const activeLanguage = (selectedModule && selectedModule.languages && selectedModule.languages.includes(selectedLanguage))
    ? selectedLanguage
    : 'en';
    
  const activeVideoFile = selectedModule && selectedModule.video
    ? (typeof selectedModule.video === 'object' ? selectedModule.video[activeLanguage] : selectedModule.video)
    : null;

  const openLightbox = (src, caption) => {
    setLightboxImage(src);
    setLightboxCaption(caption);
  };

  const closeLightbox = () => {
    setLightboxImage(null);
    setLightboxCaption('');
  };

  // Custom render components for react-markdown
  const markdownComponents = {
    // Treat pre as wrapper, let code handle structure
    pre: ({ children }) => <>{children}</>,
    code: ({ className, children, ...props }) => {
      const match = /language-(\w+)/.exec(className || '');
      const codeText = String(children).replace(/\n$/, '');
      const isInline = !className;

      if (!isInline) {
        return (
          <div className="code-block-container">
            <div className="code-block-header">
              <span>{match ? match[1].toUpperCase() : 'CODE'}</span>
              <CopyButton text={codeText} />
            </div>
            <pre className={className} style={{ margin: 0 }}>
              <code className={className} {...props}>
                {children}
              </code>
            </pre>
          </div>
        );
      }

      return (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    img: ({ src, alt, ...props }) => {
      const isAbsolute = src.startsWith('http') || src.startsWith('/');
      const finalSrc = isAbsolute ? src : `/docs/${selectedModule.key}/${src}`;
      return (
        <div style={{ position: 'relative', display: 'inline-block' }}>
          <img 
            src={finalSrc} 
            alt={alt} 
            onClick={() => openLightbox(finalSrc, alt || src)} 
            {...props} 
          />
          <button 
            className="zoom-overlay-btn"
            onClick={() => openLightbox(finalSrc, alt || src)}
            style={{
              position: 'absolute',
              bottom: '12px',
              right: '12px',
              background: 'rgba(15, 17, 37, 0.8)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '4px',
              padding: '6px',
              cursor: 'pointer',
              color: 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s'
            }}
          >
            <Maximize2 size={14} />
          </button>
        </div>
      );
    }
  };

  return (
    <div className="app-container">
      {/* 1. Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <Sparkles className="logo-icon" size={24} />
          <span className="logo-text">AI Manual Creator</span>
        </div>
        
        <div className="sidebar-search">
          <div className="search-input-wrapper">
            <Search className="search-icon" size={16} />
            <input 
              type="text" 
              placeholder="Search documentation..." 
              className="search-input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="module-list">
          {loading ? (
            <div className="no-module-selected">Loading...</div>
          ) : filteredCatalog.length === 0 ? (
            <div className="no-module-selected" style={{ fontSize: '0.9rem' }}>
              No modules found
            </div>
          ) : (
            filteredCatalog.map(module => (
              <div 
                key={module.key} 
                className={`module-item ${selectedModule?.key === module.key ? 'active' : ''}`}
                onClick={() => {
                  setSelectedModule(module);
                  setActiveTab('user');
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={16} style={{ color: selectedModule?.key === module.key ? 'var(--accent-violet)' : 'var(--text-muted)' }} />
                  <span className="module-item-title">{module.title}</span>
                </div>
                <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
              </div>
            ))
          )}
        </div>

        <div className="sidebar-footer">
          <span>Obsidian v1.0.0</span>
          <span>● Online</span>
        </div>
      </aside>

      {/* 2. Main content */}
      <main className="main-content">
        {selectedModule ? (
          <>
            <header className="main-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
                <div className="header-title-section">
                  <BookOpen size={20} className="logo-icon" />
                  <span className="header-title">{selectedModule.title} Module</span>
                </div>

                {/* Language Switcher */}
                {selectedModule.languages && selectedModule.languages.length > 1 && (
                  <div className="language-switcher" style={{
                    display: 'flex',
                    alignItems: 'center',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid var(--border-light)',
                    borderRadius: '20px',
                    padding: '3px',
                    gap: '2px'
                  }}>
                    {selectedModule.languages.map(lang => (
                      <button
                        key={lang}
                        onClick={() => setSelectedLanguage(lang)}
                        style={{
                          background: activeLanguage === lang ? 'var(--accent-violet)' : 'transparent',
                          color: activeLanguage === lang ? '#fff' : 'var(--text-secondary)',
                          border: 'none',
                          borderRadius: '16px',
                          padding: '5px 12px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          textTransform: 'uppercase'
                        }}
                      >
                        {lang === 'en' ? 'English' : lang === 'hi' ? 'हिन्दी' : lang === 'hinglish' ? 'Hinglish' : lang}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Tab Switcher */}
              <div className="tab-switcher">
                <button 
                  className={`tab-btn ${activeTab === 'user' ? 'active' : ''}`}
                  onClick={() => setActiveTab('user')}
                >
                  <Eye size={15} />
                  <span>User Guide</span>
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'technical' ? 'active' : ''}`}
                  onClick={() => setActiveTab('technical')}
                >
                  <Code size={15} />
                  <span>Technical Guide</span>
                </button>
                <button 
                  className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                  onClick={() => setActiveTab('all')}
                >
                  <FileText size={15} />
                  <span>All-in-One</span>
                </button>
              </div>
            </header>
 
            <div className="content-body">
              {/* Left Panel: Markdown Content with Embedded Video if present */}
              <div className="doc-panel">
                <div className="markdown-body">
                  {activeVideoFile && (activeTab === 'user' || activeTab === 'all') && (
                    <div className="video-walkthrough-hero" style={{
                      marginBottom: '32px',
                      background: 'linear-gradient(135deg, rgba(21, 24, 37, 0.7) 0%, rgba(15, 17, 26, 0.7) 100%)',
                      border: '1px solid var(--border-medium)',
                      borderRadius: '12px',
                      padding: '24px',
                      boxShadow: 'var(--shadow-lg), var(--glow-violet)',
                      backdropFilter: 'blur(10px)',
                      animation: 'fadeIn 0.4s ease-out'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <div style={{ 
                            background: 'rgba(139, 92, 246, 0.15)',
                            padding: '8px',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            border: '1px solid rgba(139, 92, 246, 0.2)'
                          }}>
                            <Video size={20} style={{ color: 'var(--accent-violet)', filter: 'drop-shadow(0 0 4px rgba(139, 92, 246, 0.4))' }} />
                          </div>
                          <div>
                            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600, fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>Video Walkthrough Guide</h3>
                            <p style={{ margin: '2px 0 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>Watch a neural narration of this manual</p>
                          </div>
                        </div>
                      </div>
                      
                      <div style={{ position: 'relative', width: '100%', borderRadius: '8px', overflow: 'hidden', border: '1px solid rgba(255, 255, 255, 0.05)', backgroundColor: '#000' }}>
                        <video 
                          key={`${selectedModule.key}_${activeLanguage}`}
                          src={`/docs/${selectedModule.key}/${activeVideoFile}?v=${sessionVersion}`} 
                          controls 
                          style={{ width: '100%', display: 'block', maxHeight: '420px' }}
                        />
                      </div>
                    </div>
                  )}

                  {docContent ? (
                    <ReactMarkdown components={markdownComponents}>
                      {activeContent}
                    </ReactMarkdown>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center', padding: '80px 0' }}>
                      <div className="no-module-selected">Loading guide content...</div>
                    </div>
                  )}
                </div>
              </div>


              {/* Right Panel: Media / Screenshots Sidebar */}
              <div className="media-panel">
                <h3 className="media-section-title">
                  <Terminal size={18} style={{ color: 'var(--accent-pink)' }} />
                  <span>Visual Flow Screenshots</span>
                </h3>
                
                {selectedModule.screenshots && selectedModule.screenshots.length > 0 ? (
                  <div className="media-grid">
                    {selectedModule.screenshots.map((shot, idx) => {
                      const imageSrc = `/docs/${selectedModule.key}/${shot}`;
                      // Clean label: e.g. "login_initial_state.png" -> "Login Initial State"
                      const label = shot
                        .replace(/\.\w+$/, '')
                        .replace(/_/g, ' ')
                        .replace(/\b\w/g, c => c.toUpperCase());

                      return (
                        <div 
                          key={idx} 
                          className="screenshot-card"
                          onClick={() => openLightbox(imageSrc, label)}
                        >
                          <div className="screenshot-thumbnail-wrapper">
                            <img 
                              src={imageSrc} 
                              alt={label} 
                              className="screenshot-thumbnail" 
                            />
                          </div>
                          <div className="screenshot-card-label">{label}</div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', padding: '20px 0' }}>
                    No screenshots captured for this module.
                  </div>
                )}
              </div>
            </div>
          </>
        ) : (
          <div className="no-module-selected" style={{ height: '100%' }}>
            <Sparkles size={40} className="logo-icon" style={{ animation: 'bounce 2s infinite' }} />
            <h2>AI Modular Manual Portal</h2>
            <p>Select a module from the sidebar to view generated guides.</p>
          </div>
        )}
      </main>

      {/* 3. Lightbox Modal */}
      {lightboxImage && (
        <div className="lightbox-overlay" onClick={closeLightbox}>
          <button className="lightbox-close-btn" onClick={closeLightbox}>
            <X size={20} />
          </button>
          <div className="lightbox-img-wrapper" onClick={(e) => e.stopPropagation()}>
            <img 
              src={lightboxImage} 
              alt={lightboxCaption} 
              className="lightbox-image" 
            />
          </div>
          <p className="lightbox-caption">{lightboxCaption}</p>
        </div>
      )}
    </div>
  );
}

export default App;
