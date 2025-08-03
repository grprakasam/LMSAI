import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # API Configuration
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Stripe Configuration
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'generated_audio')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///r_tutor_dev.db'
    SESSION_COOKIE_SECURE = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///r_tutor_prod.db'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Subscription Plans Configuration
PLANS = {
    'free': {
        'tutorials_per_month': 3,
        'price': 0,
        'stripe_price_id': None,
        'features': [
            'Basic R topics',
            'Standard content quality',
            'Community support',
            'Web access only'
        ]
    },
    'pro': {
        'tutorials_per_month': 50,
        'price': 9,
        'stripe_price_id': os.environ.get('STRIPE_PRO_PRICE_ID'),
        'features': [
            'All R topics + advanced',
            'Premium AI-generated content',
            'Audio tutorial generation',
            'Code execution environment',
            'Export to PDF/Audio',
            'Priority support'
        ]
    },
    'team': {
        'tutorials_per_month': 200,
        'price': 29,
        'stripe_price_id': os.environ.get('STRIPE_TEAM_PRICE_ID'),
        'features': [
            'Everything in Pro',
            'Team management dashboard',
            'Usage analytics',
            'Custom R topics',
            'API access',
            'Dedicated support'
        ]
    }
}

# R Topics Content Configuration
R_TOPICS_CONTENT = {
    'free_topics': {
        'data structures': {
            'beginner': {
                'concepts': ['vectors', 'lists', 'data frames', 'matrices'],
                'code_examples': [
                    '# Creating vectors\nnumeric_vector <- c(1, 2, 3, 4, 5)\ncharacter_vector <- c("R", "is", "awesome")',
                    '# Creating data frames\ndf <- data.frame(\n  name = c("Alice", "Bob", "Charlie"),\n  age = c(25, 30, 35),\n  city = c("NYC", "LA", "Chicago")\n)'
                ],
                'packages': ['base', 'utils'],
                'learning_objectives': [
                    'Understanding R fundamental data types',
                    'Creating and manipulating vectors',
                    'Working with data frames effectively'
                ]
            },
            'intermediate': {
                'concepts': ['advanced indexing', 'data manipulation', 'merging datasets'],
                'code_examples': [
                    '# Advanced indexing\ndf[df$age > 25 & df$city == "NYC", ]',
                    '# Merging datasets\nmerged_df <- merge(df1, df2, by = "id")'
                ],
                'packages': ['base', 'utils'],
                'learning_objectives': [
                    'Mastering data frame operations',
                    'Understanding complex indexing',
                    'Merging and joining datasets'
                ]
            }
        },
        'basic plotting': {
            'beginner': {
                'concepts': ['plot function', 'basic charts', 'customization'],
                'code_examples': [
                    '# Basic scatter plot\nplot(x, y, main="My Plot", xlab="X axis", ylab="Y axis")',
                    '# Histogram\nhist(data$variable, breaks=20, col="blue")'
                ],
                'packages': ['graphics', 'grDevices'],
                'learning_objectives': [
                    'Creating basic plots in R',
                    'Understanding plot customization',
                    'Using different chart types'
                ]
            }
        }
    },
    'premium_topics': {
        'advanced ggplot2': {
            'intermediate': {
                'concepts': ['grammar of graphics', 'layered approach', 'themes'],
                'code_examples': [
                    '# Advanced ggplot\nggplot(data, aes(x=var1, y=var2)) +\n  geom_point(aes(color=factor(group))) +\n  theme_minimal() +\n  labs(title="Advanced Visualization")'
                ],
                'packages': ['ggplot2', 'scales', 'RColorBrewer'],
                'learning_objectives': [
                    'Mastering ggplot2 grammar',
                    'Creating publication-ready plots',
                    'Advanced customization techniques'
                ]
            },
            'expert': {
                'concepts': ['custom themes', 'complex layouts', 'animations'],
                'code_examples': [
                    '# Custom theme and faceting\nggplot(data) + \n  geom_point() + \n  facet_wrap(~category) +\n  theme_custom() +\n  transition_reveal(time)'
                ],
                'packages': ['ggplot2', 'gganimate', 'patchwork', 'gridExtra'],
                'learning_objectives': [
                    'Building custom visualization themes',
                    'Creating animated plots',
                    'Complex multi-panel layouts'
                ]
            }
        },
        'machine learning': {
            'intermediate': {
                'concepts': ['supervised learning', 'model evaluation', 'cross-validation'],
                'code_examples': [
                    '# Basic ML workflow\nlibrary(caret)\nmodel <- train(target ~ ., data=train_data, method="rf")\npredictions <- predict(model, test_data)'
                ],
                'packages': ['caret', 'randomForest', 'e1071'],
                'learning_objectives': [
                    'Understanding ML workflow in R',
                    'Model training and evaluation',
                    'Cross-validation techniques'
                ]
            },
            'expert': {
                'concepts': ['ensemble methods', 'hyperparameter tuning', 'feature engineering'],
                'code_examples': [
                    '# Advanced ML pipeline\nlibrary(tidymodels)\nrf_spec <- rand_forest(trees = 1000) %>%\n  set_engine("ranger") %>%\n  set_mode("regression")'
                ],
                'packages': ['tidymodels', 'ranger', 'xgboost', 'glmnet'],
                'learning_objectives': [
                    'Advanced ML algorithms implementation',
                    'Automated hyperparameter tuning',
                    'Building ML pipelines'
                ]
            }
        },
        'shiny dashboards': {
            'intermediate': {
                'concepts': ['reactive programming', 'UI layouts', 'server logic'],
                'code_examples': [
                    '# Shiny app structure\nui <- fluidPage(\n  titlePanel("My Dashboard"),\n  sidebarLayout(...)\n)\nserver <- function(input, output) {...}'
                ],
                'packages': ['shiny', 'shinydashboard', 'DT'],
                'learning_objectives': [
                    'Building interactive web applications',
                    'Understanding reactive programming',
                    'Creating responsive dashboards'
                ]
            },
            'expert': {
                'concepts': ['custom inputs', 'modules', 'deployment'],
                'code_examples': [
                    '# Shiny modules\nmoduleUI <- function(id) {\n  ns <- NS(id)\n  tagList(...)\n}\nmoduleServer <- function(id) {\n  moduleServer(id, function(input, output, session) {...})\n}'
                ],
                'packages': ['shiny', 'shinydashboard', 'shinyWidgets', 'plotly'],
                'learning_objectives': [
                    'Building modular Shiny applications',
                    'Advanced UI customization',
                    'Production deployment strategies'
                ]
            }
        },
        'statistical modeling': {
            'expert': {
                'concepts': ['linear models', 'generalized linear models', 'mixed effects'],
                'code_examples': [
                    '# Advanced statistical modeling\nlibrary(lme4)\nmodel <- lmer(response ~ fixed_effect + (1|random_effect), data=data)\nsummary(model)'
                ],
                'packages': ['lme4', 'nlme', 'broom', 'modelr'],
                'learning_objectives': [
                    'Advanced statistical modeling techniques',
                    'Mixed effects models',
                    'Model diagnostics and validation'
                ]
            }
        }
    }
}