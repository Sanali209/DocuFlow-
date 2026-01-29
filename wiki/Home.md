# Welcome to DocuFlow Wiki

Welcome to the official documentation for **DocuFlow** - a modern, AI-powered document management system.

## 🚀 Quick Start

New to DocuFlow? Start here:
1. [Getting Started Guide](Getting-Started.md) - Installation and first steps
2. [User Guide](User-Guide.md) - Learn how to use DocuFlow
3. [API Documentation](API-Documentation.md) - REST API reference

## 📚 Documentation Sections

### For Users
- **[Getting Started](Getting-Started.md)** - Set up and run DocuFlow
- **[User Guide](User-Guide.md)** - Complete feature walkthrough
- **[FAQ & Troubleshooting](FAQ-and-Troubleshooting.md)** - Common issues and solutions

### For Developers
- **[Developer Guide](Developer-Guide.md)** - Development setup and workflow
- **[API Documentation](API-Documentation.md)** - REST API endpoints and examples
- **[Architecture Overview](Architecture.md)** - System design and components
- **[Contributing Guidelines](Contributing.md)** - How to contribute

### For DevOps
- **[Deployment Guide](Deployment-Guide.md)** - Production deployment instructions
- **[Configuration Guide](Configuration.md)** - Environment variables and settings
- **[Monitoring Guide](Monitoring.md)** - Health checks and observability

## 🎯 What is DocuFlow?

DocuFlow is a comprehensive document management system that combines:
- **Smart Document Tracking** - Organize and track documents with rich metadata
- **AI-Powered OCR** - Extract text and tables from images/PDFs using IBM Docling
- **Task Management** - Embedded task lists with assignee tracking
- **Advanced Search** - Multi-criteria filtering with saved presets
- **Mobile-First Design** - Fully responsive interface optimized for all devices

## 🏗️ Architecture at a Glance

```
┌─────────────────────────────────────────┐
│     Frontend (Svelte 5 + Vite)         │
│          Modern Reactive UI             │
└────────────────┬────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────┐
│      Backend (FastAPI + SQLite)        │
│        Business Logic & Storage         │
└────────────────┬────────────────────────┘
                 │ HTTP Requests
┌────────────────▼────────────────────────┐
│   OCR Service (Docling + FastAPI)     │
│      Document Understanding AI          │
└─────────────────────────────────────────┘
```

## 🔗 Quick Links

- **[Main README](../README.md)** - Project overview
- **[Design Document](../designdoc.md)** - Detailed architecture and design
- **[GitHub Repository](https://github.com/Sanali209/DocuFlow-)** - Source code
- **[Issue Tracker](https://github.com/Sanali209/DocuFlow-/issues)** - Report bugs or request features

## 📖 Documentation Sections

| Section | Description |
|---------|-------------|
| [Getting Started](Getting-Started.md) | Installation, setup, and first run |
| [User Guide](User-Guide.md) | Feature walkthrough and usage examples |
| [Developer Guide](Developer-Guide.md) | Development environment and workflow |
| [API Documentation](API-Documentation.md) | REST API reference with examples |
| [Deployment Guide](Deployment-Guide.md) | Production deployment strategies |
| [Configuration](Configuration.md) | Environment variables and settings |
| [Architecture](Architecture.md) | System design and technical details |
| [FAQ](FAQ-and-Troubleshooting.md) | Common questions and solutions |
| [Contributing](Contributing.md) | How to contribute to the project |

## 🤝 Community & Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/Sanali209/DocuFlow-/issues)
- 📧 **Email Support**: [Your Email]
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Sanali209/DocuFlow-/discussions)

## 📝 Recent Updates

Check the [CHANGELOG](../CHANGELOG.md) for the latest updates and releases.

## 📄 License

DocuFlow is open-source software licensed under the [MIT License](../LICENSE).

---

**Last Updated**: 2026-01-29  
**Wiki Version**: 1.0  
**DocuFlow Version**: 1.0.0
