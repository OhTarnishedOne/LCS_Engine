# Probability Lab Module

## Overview
The Probability Lab is an AI-powered educational module that teaches probabilistic thinking through real prediction market exercises using Kalshi's public API. It helps users develop better calibration - the ability to accurately assess the likelihood of future events.

## Features

### 🎯 Core Functionality
- **Real-time prediction markets** from Kalshi API (no authentication required)
- **Intelligent question selection** based on user interests and skill level
- **Instant feedback** comparing predictions to market consensus
- **Calibration scoring** using Brier scores to track accuracy
- **Cognitive bias detection** and personalized learning

### 🧠 Agent Architecture
The module uses an autonomous agent that:
- **Plans**: Selects appropriate markets based on student profile
- **Executes**: Presents predictions and captures responses
- **Reflects**: Identifies patterns and adjusts teaching strategy
- **Teaches**: Explains biases and concepts when needed

### 📊 Dashboard & Analytics
- **Calibration curve**: Shows if your confidence matches accuracy
- **Rolling Brier score**: Tracks improvement over time
- **Domain performance**: Identifies strengths/weaknesses by category
- **You vs. Market**: Compares your accuracy to market baseline

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Application
```bash
streamlit run streamlit_ui/app.py
```

### 3. Navigate to Probability Lab
Click "🧠 Probability Lab" in the sidebar navigation

### 4. Configure Your Profile
- Select skill level (beginner/intermediate/advanced)
- Choose interest categories
- Set session length (5-20 predictions)

### 5. Start Practicing!
- Read prediction questions
- Estimate probability (0-100%)
- Optionally explain reasoning
- Get instant feedback
- Track your calibration

## Architecture

```
streamlit_ui/
├── pages/
│   └── 4_Probability_Lab.py      # Main Streamlit page
├── agents/
│   └── probability_agent.py      # Autonomous teaching agent
├── tools/
│   ├── kalshi_client.py         # Kalshi API wrapper
│   └── calibration.py          # Brier scoring utilities
└── test_kalshi.py              # API test script
```

## How It Works

### Prediction Flow
1. Agent selects market based on your profile
2. You make a probability prediction
3. System compares to market consensus
4. Prediction stored with timestamp
5. Agent provides contextual feedback
6. When markets resolve, scores calculated

### Calibration Scoring
Uses the Brier Score formula: `(prediction - outcome)²`
- 0 = Perfect prediction
- 0.25 = Random guessing
- 1 = Worst possible

### Cognitive Biases Detected
- **Overconfidence**: Too many extreme predictions
- **Anchoring**: Predictions too close to market
- **Base rate neglect**: Ignoring historical frequencies
- **Systematic bias**: Consistent over/under estimation

## API Details

### Kalshi Public Endpoints Used
- `GET /markets` - List active prediction markets
- `GET /markets/{ticker}` - Get specific market details
- `GET /events` - Get event categories

Base URL: `https://api.elections.kalshi.com/trade-api/v2`

**Note**: Despite the "elections" subdomain, this API provides ALL Kalshi markets including economics, technology, climate, sports, etc.

### Rate Limiting
- Minimum 200ms between requests
- Graceful fallback on API failures
- Caches market data to reduce calls

## Session State Structure
```python
st.session_state.probability_lab = {
    'student_id': str,              # Unique identifier
    'skill_level': str,             # beginner/intermediate/advanced
    'interests': List[str],         # Selected categories
    'predictions': List[Prediction], # All predictions made
    'calibration': {
        'overall_brier': float,      # Overall accuracy score
        'rolling_brier': List[float], # Recent performance
        'by_domain': Dict[str, float], # Category scores
        'vs_market_baseline': Dict   # Comparison metrics
    },
    'agent_state': {
        'predictions_this_session': int,
        'target_predictions': int,
        'domains_covered_this_session': List[str],
        'current_market': Dict
    }
}
```

## Testing

### Test Kalshi API
```bash
cd streamlit_ui
python test_kalshi.py
```

### Expected Output
- ✅ Found open markets
- ✅ Got event categories
- ✅ Resolution check completed

## Educational Content

### Topics Covered
- **Calibration basics** - Matching confidence to accuracy
- **Cognitive biases** - Common prediction errors
- **Base rates** - Historical frequencies
- **Market efficiency** - When to trust consensus
- **Brier scoring** - Understanding the metric

### Learning Progression
1. **Beginner**: Focus on diverse, lower-stakes predictions
2. **Intermediate**: Mix of efficient and inefficient markets
3. **Advanced**: High-volume markets, complex topics

## Future Enhancements

### Database Migration
Currently uses `st.session_state` for storage. Architecture ready for SQLite/PostgreSQL:
- Abstract repository pattern implemented
- Prediction dataclass for ORM mapping
- Clean separation of concerns

### Potential Features
- [ ] Historical prediction review
- [ ] Head-to-head competitions
- [ ] Custom market creation
- [ ] Advanced statistics (ROC curves, etc.)
- [ ] LLM-generated market summaries
- [ ] Email notifications for resolutions

## Troubleshooting

### Common Issues

**"No markets found"**
- Check internet connection
- Verify Kalshi API is accessible
- Try different categories

**"API request failed"**
- Rate limit may be hit
- Wait a moment and retry
- Check Kalshi service status

**Session state lost**
- Use shareable link to persist
- Predictions auto-save to session

## Demo for W!se (Feb 3rd)

### Key Points to Highlight
1. **Real markets** - Live data, not simulations
2. **AI guidance** - Intelligent question selection
3. **Instant feedback** - Learn from every prediction
4. **Track progress** - See calibration improve
5. **No risk** - Educational only, no money involved

### Demo Flow (5 minutes)
1. Quick intro to prediction markets
2. Make 3-5 predictions
3. Show calibration dashboard
4. Explain a cognitive bias
5. Highlight learning value

## Support

For issues or questions:
- Check existing GitHub issues
- Test Kalshi API with test script
- Verify all dependencies installed
- Review session state structure

## Credits

Built for LCS Engine by the team
Using Kalshi's public prediction market API
Calibration scoring based on Brier (1950)
Cognitive bias framework from Kahneman & Tversky