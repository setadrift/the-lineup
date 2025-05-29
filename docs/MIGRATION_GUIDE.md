# Migration Guide: Streamlit MVP → Production Stack

## Overview

This document outlines the key business logic, algorithms, and features from the Streamlit MVP that need to be migrated to the new FastAPI + Next.js production stack.

## Core Business Logic to Migrate

### 1. Draft Analytics & Scoring System

**Location in MVP**: `legacy_streamlit/streamlit_components/draft_logic.py`

**Key Components**:
- `CategoryAnalyzer` class - 9-category fantasy basketball analysis
- `PickSuggestionEngine` - AI-powered pick recommendations
- `DraftAnalytics` - Post-draft team analysis and grading
- Z-score calculation and normalization across categories

**Migration Priority**: HIGH - This is the core value proposition

**New Architecture**:
```
backend/app/core/analytics/
├── category_analyzer.py
├── pick_suggestions.py
├── draft_analytics.py
└── scoring_engine.py
```

### 2. Player Data & Statistics

**Location in MVP**: `app/nba/` and database utilities

**Key Components**:
- Player stats normalization (z-scores)
- Historical trend analysis
- Player comparison algorithms
- NBA API integration for real-time data

**Migration Priority**: HIGH - Required for all features

**New Architecture**:
```
backend/app/services/
├── player_service.py
├── stats_service.py
└── nba_api_service.py
```

### 3. Draft State Management

**Location in MVP**: `legacy_streamlit/streamlit_components/draft_logic.py`

**Key Components**:
- `DraftState` class - Serpentine draft order management
- Draft progression logic
- Team roster management
- AI opponent behavior

**Migration Priority**: HIGH - Core functionality

**New Architecture**:
```
backend/app/core/draft/
├── draft_manager.py
├── draft_state.py
└── ai_opponents.py
```

### 4. User Interface Components

**Location in MVP**: `legacy_streamlit/streamlit_components/ui_components.py`

**Key Components**:
- Draft dashboard layouts
- Player comparison tools
- Category analysis displays
- Team projection cards
- Historical trends visualization

**Migration Priority**: MEDIUM - UI will be redesigned but logic preserved

**New Architecture**:
```
frontend/components/
├── draft/
├── analytics/
├── player-comparison/
└── shared/
```

## Database Schema Migration

### Current Tables (to be enhanced)
- `player_stats` - Season statistics
- `player_game_stats` - Game-by-game data
- `team_schedule` - NBA team schedules
- `player_features` - Calculated features and z-scores

### New Tables Required
```sql
-- User management
user_accounts
user_subscriptions
user_preferences

-- League management
leagues
league_members
league_settings

-- Draft management
draft_sessions
draft_picks
draft_state

-- Analytics & history
user_draft_history
team_performance_history
```

## Key Algorithms to Port

### 1. Z-Score Calculation Engine

**Current Implementation**: 
```python
# From legacy CategoryAnalyzer
def calculate_z_scores(self, player_stats):
    # Standardize stats across 9 categories
    # Handle different stat directions (turnovers negative)
```

**Migration Notes**:
- Convert to async for database operations
- Add caching for frequently accessed calculations
- Implement batch processing for league-wide calculations

### 2. Pick Suggestion Algorithm

**Current Implementation**:
```python
# From PickSuggestionEngine
def get_suggestions(self, available_players, user_roster, ...):
    # Multi-factor scoring:
    # - Position scarcity
    # - Team needs analysis
    # - Value vs ADP
    # - Category balance
    # - Punt strategy detection
```

**Migration Notes**:
- Add machine learning components
- Implement user preference learning
- Add league-specific recommendation tuning

### 3. Punt Strategy Detection

**Current Implementation**:
```python
def detect_punt_strategies(self, roster_ids, ...):
    # Conservative detection of intentional category punting
    # Confidence levels and strategic recommendations
```

**Migration Notes**:
- Enhance with historical user behavior
- Add league-wide strategy analysis
- Implement dynamic threshold adjustment

## User Experience Flows

### 1. Draft Room Experience
**Current**: Single-user mock draft with AI opponents
**Target**: Multi-user real-time draft rooms with WebSocket support

### 2. Player Analysis
**Current**: Detailed comparison tools and historical trends
**Target**: Enhanced with social features, notes, and sharing

### 3. Team Analytics
**Current**: Post-draft analysis and projections
**Target**: Season-long tracking with live updates

## Authentication & User Management

**Current**: None (single-user)
**Target**: 
- User registration/login
- Subscription management (Stripe)
- League creation and management
- Social features (friends, league chat)

## API Endpoints to Implement

### Core Endpoints
```
GET  /api/v1/players - List players with filters
GET  /api/v1/players/{id}/stats - Player statistics
POST /api/v1/players/compare - Compare multiple players
GET  /api/v1/draft-suggestions - Get pick recommendations
POST /api/v1/leagues - Create new league
GET  /api/v1/leagues/{id}/draft - Live draft data
POST /api/v1/draft/{id}/pick - Make draft pick
```

### Analytics Endpoints
```
GET  /api/v1/analytics/team-projections
GET  /api/v1/analytics/league-standings
GET  /api/v1/analytics/player-trends
POST /api/v1/analytics/compare-teams
```

## Performance Considerations

### Caching Strategy
- Redis for frequently accessed player data
- League-specific caching for draft suggestions
- Precomputed z-scores and rankings

### Database Optimization
- Proper indexing for player lookups
- Materialized views for complex analytics
- Connection pooling for concurrent users

## Testing Strategy

### Unit Tests
- All algorithm components
- Database models and operations
- API endpoint functionality

### Integration Tests
- End-to-end draft flows
- Multi-user scenarios
- Payment processing

### Load Testing
- Concurrent draft rooms
- Real-time analytics updates
- Database performance under load

## Migration Phases

### Phase 1: Foundation (Current)
- [x] Project structure setup
- [x] FastAPI application skeleton
- [x] Database configuration
- [ ] Core models definition

### Phase 2: Core Logic
- [ ] Port analytics algorithms
- [ ] Implement player data services
- [ ] Create draft management system
- [ ] Basic API endpoints

### Phase 3: User Management
- [ ] Authentication system
- [ ] User registration/login
- [ ] Subscription management
- [ ] League creation

### Phase 4: Real-time Features
- [ ] WebSocket draft rooms
- [ ] Live analytics updates
- [ ] Social features

### Phase 5: Frontend
- [ ] Next.js application setup
- [ ] Core UI components
- [ ] API integration
- [ ] Mobile optimization

### Phase 6: Production
- [ ] Deployment setup
- [ ] Monitoring and logging
- [ ] Performance optimization
- [ ] Security hardening

## Notes for Development

- Keep all legacy Streamlit code in `legacy_streamlit/` for reference
- Extract pure business logic functions first (no UI dependencies)
- Test algorithms independently before API integration
- Consider backward compatibility for data formats
- Document any changes to algorithm behavior 