# R Tutor Pro - AI-Powered R Learning SaaS

A modern, interactive web application designed specifically for R developers to generate personalized audio tutorials based on their expertise level and learning preferences.

## 🌟 Features

### 🎯 R Developer-Focused
- **AI-Powered Content**: Advanced AI generates personalized tutorials based on your expertise level and learning goals
- **Interactive R Code**: Learn with real R code examples and hands-on exercises tailored to your skill level
- **Audio Tutorials**: Listen to your tutorials on-the-go with AI-generated audio narration (Pro feature)
- **Progress Tracking**: Monitor your learning journey with detailed analytics and skill progression insights

### 🎨 Modern & Professional Design
- **Gradient Background**: Beautiful purple-blue gradient with glassmorphism effects
- **Interactive Elements**: Hover effects, animations, and smooth transitions
- **R-Themed Colors**: Blue color scheme matching R programming aesthetics
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices

### 🔧 Advanced Features
- **Subscription Plans**: Free, Pro, and Team plans with different feature sets
- **Team Learning**: Collaborate with your team and track organizational R skill development
- **Usage Analytics**: Detailed analytics dashboard for tracking progress
- **API Access**: RESTful API for programmatic access (Team plan)

## 🚀 Technology Stack

- **Backend**: Python Flask with SQLAlchemy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Flask-Login with session management
- **AI Services**: DeepSeek API / OpenAI API integration
- **Deployment**: Docker, Docker Compose, Nginx, Gunicorn
- **Monitoring**: Health checks, logging, and performance metrics

## 📁 Project Structure

```
LMSAI/
├── app.py                 # Flask application entry point
├── run.py                 # Development server runner
├── config.py              # Configuration settings
├── models.py              # Database models
├── routes.py              # Route definitions
├── utils.py               # Utility functions
├── content.py             # R topics content
├── services.py            # AI and audio services
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .env.example          # Environment variables template
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── nginx.conf            # Nginx configuration
├── deployment_config.txt # Deployment configurations
├── api_tests.py          # API tests and documentation
├── templates/            # HTML templates
│   ├── index.html        # Landing page
│   ├── dashboard.html    # User dashboard
│   ├── auth.html         # Authentication page
│   ├── pricing.html      # Pricing page
│   ├── billing.html      # Billing page
│   ├── contact.html      # Contact page
│   ├── privacy.html      # Privacy policy
│   ├── terms.html        # Terms of service
│   ├── error.html        # Error page
│   └── tutorial.html     # Tutorial view page
├── static/               # Static assets
│   ├── style.css         # Main stylesheet
│   └── generated_audio/  # Generated audio files
├── instance/             # SQLite database (development)
├── logs/                 # Application logs
└── tests/                # Test files
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- pip
- Docker (optional, for containerized deployment)

### Local Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/grprakasam/LMSAI.git
   cd LMSAI
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**:
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

5. **Initialize Database**:
   ```bash
   python run.py --init-db
   ```

6. **Run the Application**:
   ```bash
   python run.py
   ```

7. **Access the Application**:
   Open your browser and navigate to `http://localhost:5000`

## 🎮 How to Use

### For End Users
1. **Register/Login**: Create an account or sign in to access the dashboard
2. **Select a Topic**: Choose from popular R topics or enter your own
3. **Choose Expertise Level**: Beginner, Intermediate, or Expert
4. **Set Duration**: Select tutorial length (1-15 minutes)
5. **Generate Tutorial**: Click "Generate Tutorial" to create personalized content
6. **View Results**: Access generated tutorials with R code examples
7. **Upgrade**: Consider upgrading to Pro/Team plan for advanced features

### For Developers
1. **API Documentation**: Check `api_tests.py` for detailed API documentation
2. **Customization**: Modify `content.py` to add new R topics
3. **Styling**: Update `static/style.css` for design changes
4. **Deployment**: Use Docker Compose for production deployment

## 🎨 Design Features

### Color Scheme
- **Primary**: Blue gradient (#667eea, #764ba2)
- **Secondary**: Blue (#2196F3) and Green (#4CAF50)
- **Background**: Purple-blue gradient
- **Interactive**: Gradient buttons with hover effects

### Interactive Elements
- **Hover Effects**: Smooth transitions and elevation changes
- **Form Validation**: Real-time feedback and error handling
- **Loading States**: Animated spinners with R-themed messages
- **Responsive Layout**: Adapts to all screen sizes

## 🔧 Customization

The application can be easily customized:

- **Add New Topics**: Extend `R_TOPICS_CONTENT` in `content.py`
- **Modify Styling**: Update `static/style.css` for design changes
- **Add Features**: Enhance templates in the `templates/` directory
- **Integrate APIs**: Connect to real audio generation services in `services.py`

## 🌐 Browser Compatibility

- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+

## 📱 Mobile Support

Fully responsive design with:
- Touch-friendly interface
- Optimized layouts for small screens
- Swipe gestures support
- Mobile-first approach

## 🎯 Target Audience

- **R Beginners**: Learning R programming fundamentals
- **Data Scientists**: Using R for data analysis and visualization
- **Statisticians**: Applying R for statistical modeling
- **Researchers**: Using R for academic and scientific research
- **Developers**: Building R packages and applications

## 🚀 Deployment

### Docker Deployment (Recommended)
```bash
docker-compose up -d
```

### Manual Deployment
```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## 🧪 Testing

### Run Unit Tests
```bash
python -m pytest tests/ -v
```

### Run Load Tests
```bash
locust -f load_test.py --host=http://localhost:5000
```

## 📊 Monitoring

- Health check endpoint: `/health`
- Usage analytics: `/api/analytics`
- System metrics: `/api/metrics`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- R community for inspiration
- Flask framework for the backend
- DeepSeek/OpenAI for AI capabilities
- All contributors and users

---

**Built with ❤️ for the R programming community**
