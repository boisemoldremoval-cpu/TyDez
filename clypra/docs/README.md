# Clypra Documentation

Welcome to the Clypra documentation directory. This folder contains comprehensive guides for developers, testers, and contributors.

## 📚 Documentation Index

### For Developers

- **[GEMINI.md](./GEMINI.md)** - AI Developer Guidelines & Project Rules
  - Core technology stack
  - Frontend & UI design rules
  - Backend Rust rules
  - CI/CD & cross-compilation guidelines
  - Dependency management

### For Testers

- **[MANUAL_TESTING_GUIDE.md](./MANUAL_TESTING_GUIDE.md)** - Complete End-to-End Testing Guide
  - Launch screen & project setup
  - Media import & management
  - Timeline operations
  - Video playback & preview
  - Audio features
  - Text & titles
  - Export & rendering
  - Performance & stability

### For Feature Development

- **[VIDEO_EFFECTS_CHECKLIST.md](./VIDEO_EFFECTS_CHECKLIST.md)** - Video Effects Implementation Checklist
  - Core system implementation
  - Backend implementation
  - UI components
  - Timeline integration
  - Rendering pipeline
  - Export pipeline
  - Performance optimization

- **[video-effects/VIDEO_EFFECTS_ARCHITECTURE.md](./video-effects/VIDEO_EFFECTS_ARCHITECTURE.md)** - Video Effects Architecture
  - System architecture diagrams
  - Component interactions
  - Data flow

## 🗂️ Project Documentation Structure

```
docs/
├── README.md                           # This file - Documentation index
├── GEMINI.md                          # AI development guidelines
├── MANUAL_TESTING_GUIDE.md            # Testing procedures
├── VIDEO_EFFECTS_CHECKLIST.md         # Feature implementation checklist
└── video-effects/
    └── VIDEO_EFFECTS_ARCHITECTURE.md  # Video effects architecture
```

## 🚀 Quick Links

### Root Documentation

- [Main README](../README.md) - Project overview and getting started
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md) - Community guidelines
- [CHANGELOG.md](../CHANGELOG.md) - Version history
- [LICENSE](../LICENSE) - MIT License

### Development Resources

- [Scripts](../scripts/) - Development scripts and tools

## 📝 Documentation Guidelines

When adding new documentation:

1. **Choose the right location:**
   - General guides → `/docs/`
   - Feature-specific docs → `/docs/[feature-name]/`
   - API documentation → Keep with the code in `/src/`

2. **Use clear naming:**
   - Use UPPER_CASE for important guides (GEMINI.md, README.md)
   - Use descriptive names (MANUAL_TESTING_GUIDE.md, not TESTING.md)

3. **Keep it organized:**
   - Add new docs to this index
   - Link related documents
   - Use consistent formatting

4. **Write for your audience:**
   - Developers need code examples and architecture
   - Testers need step-by-step procedures
   - Users need simple how-to guides

## 🤝 Contributing to Documentation

Found a typo or want to improve our docs? We welcome contributions!

1. Edit the documentation file
2. Submit a pull request
3. Follow our [Contributing Guide](../CONTRIBUTING.md)

---

**Last Updated:** June 2026
