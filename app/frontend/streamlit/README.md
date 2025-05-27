# The Lineup - Frontend Architecture

## 🏗️ Modular Structure

This directory contains the modular frontend architecture for The Lineup draft assistant, following best programming practices and The Lineup's design principles.

## 📁 Directory Structure

```
app/frontend/streamlit/
├── components/           # Reusable UI and logic components
│   ├── draft_logic.py   # Draft state management and AI suggestions
│   └── ui_components.py # Streamlit UI components
├── pages/               # Main application pages
│   ├── draft_assistant.py     # Original monolithic version
│   └── draft_assistant_v2.py  # New modular version
├── styles/              # CSS stylesheets
│   └── main.css        # Main stylesheet with design system
├── utils/               # Utility modules
│   ├── database.py     # Database operations and caching
│   └── styling.py      # CSS loading and theme utilities
└── README.md           # This file
```

## 🧩 Component Overview

### `components/draft_logic.py`
- **DraftState**: Manages draft progression and state
- **PickSuggestionEngine**: Generates intelligent pick suggestions with reasoning
- **AIOpponent**: Handles AI opponent drafting logic
- Helper functions for draft initialization and player filtering

### `components/ui_components.py`
- Reusable Streamlit interface components
- Page configuration and styling setup
- Pick suggestion displays with priority-based styling
- Player selection interfaces and roster displays
- Draft status and progress indicators

### `utils/database.py`
- Centralized database operations with caching
- Player pool queries with z-scores and ADP data
- Detailed player statistics retrieval
- Connection validation and error handling

### `utils/styling.py`
- CSS loading and application utilities
- Theme color management
- Centralized styling functions

### `styles/main.css`
- Complete design system with CSS variables
- Responsive design for mobile and desktop
- Component-specific styling (buttons, tables, suggestions)
- Professional color scheme and typography

## 🚀 Usage

### Running the Modular Version
```bash
# From project root
python run_draft_v2.py

# Or directly with streamlit
streamlit run app/frontend/streamlit/pages/draft_assistant_v2.py --server.port 8502
```

### Key Features
- **Intelligent Pick Suggestions**: AI-powered recommendations with detailed reasoning
- **Position Scarcity Analysis**: Real-time evaluation of position availability
- **Value-based Drafting**: ADP comparison and value identification
- **Team Need Assessment**: Smart suggestions based on roster composition
- **Responsive Design**: Mobile-first UI with professional styling

## 🎯 Design Principles Applied

1. **Modular Architecture**: Each component has a single responsibility
2. **Database-first Development**: Centralized data operations with caching
3. **Readable & Maintainable**: Clear separation of concerns
4. **Production-ready**: Error handling and validation throughout
5. **Responsive Design**: Mobile-optimized interface

## 🔧 Configuration

The application uses environment variables for database configuration:
- `DATABASE_URL`: PostgreSQL connection string

CSS variables in `styles/main.css` control the design system:
- `--primary-orange`: #FF6B35
- `--primary-blue`: #2E86AB
- `--secondary-orange`: #F7931E

## 📈 Performance Features

- **Streamlit Caching**: Database queries cached for 5 minutes
- **Efficient Queries**: Optimized SQL with proper indexing
- **Lazy Loading**: Components loaded only when needed
- **Responsive Images**: CSS optimizations for mobile

## 🧪 Testing

The modular structure makes testing easier:
- Individual components can be unit tested
- Database operations are isolated and mockable
- UI components are reusable across different pages

## 🔮 Future Enhancements

The modular structure supports easy addition of:
- Live draft integration
- Advanced analytics dashboard
- Custom league settings
- LLM-powered insights
- Multi-sport support

## 📝 Migration Notes

To migrate from the original `draft_assistant.py`:
1. The new version maintains all existing functionality
2. Improved performance through better caching
3. Enhanced mobile experience
4. More maintainable codebase
5. Easier to extend with new features

The original file remains available for reference and can be deprecated once the new version is fully tested. 