import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-r-tutor-pro'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # API Configuration
    DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
    
    # Email Configuration (for future notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Stripe Configuration (for future payment integration)
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Redis Configuration (for future caching/sessions)
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'generated_audio')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Application Settings
    ITEMS_PER_PAGE = 10
    MAX_TUTORIAL_DURATION = 60  # minutes
    MIN_TUTORIAL_DURATION = 1   # minutes

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///r_tutor_dev.db'
    SESSION_COOKIE_SECURE = False
    
    # Development-specific settings
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries
    WTF_CSRF_ENABLED = False
    
    # Relaxed rate limits for development
    RATELIMIT_ENABLED = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///r_tutor_prod.db'
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Production logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    
    # Enable rate limiting
    RATELIMIT_ENABLED = True

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
            'Web access only',
            '5-minute tutorial limit'
        ],
        'limits': {
            'max_duration': 5,
            'audio_generation': False,
            'premium_topics': False,
            'api_access': False,
            'export_options': False
        }
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
            'Up to 60-minute tutorials',
            'Priority support'
        ],
        'limits': {
            'max_duration': 60,
            'audio_generation': True,
            'premium_topics': True,
            'api_access': False,
            'export_options': True
        }
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
            'Bulk export options',
            'Dedicated support',
            'Team collaboration tools'
        ],
        'limits': {
            'max_duration': 60,
            'audio_generation': True,
            'premium_topics': True,
            'api_access': True,
            'export_options': True,
            'team_management': True
        }
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
        },
        'statistics basics': {
            'beginner': {
                'concepts': ['descriptive statistics', 'correlation', 'basic tests'],
                'code_examples': [
                    '# Descriptive statistics\nsummary(data)\nmean(data$column, na.rm = TRUE)\nsd(data$column, na.rm = TRUE)',
                    '# Correlation and basic tests\ncor(data$x, data$y, use = "complete.obs")\nt.test(data$group1, data$group2)'
                ],
                'packages': ['stats', 'base'],
                'learning_objectives': [
                    'Understanding descriptive statistics',
                    'Calculating correlations',
                    'Performing basic hypothesis tests'
                ]
            },
            'intermediate': {
                'concepts': ['ANOVA', 'regression', 'model diagnostics'],
                'code_examples': [
                    '# Linear regression\nmodel <- lm(y ~ x1 + x2, data = data)\nsummary(model)',
                    '# ANOVA\nanova_result <- aov(value ~ group, data = data)\nsummary(anova_result)'
                ],
                'packages': ['stats', 'broom'],
                'learning_objectives': [
                    'Building linear models',
                    'Understanding ANOVA',
                    'Model diagnostics and interpretation'
                ]
            }
        },
        'data import': {
            'beginner': {
                'concepts': ['reading CSV', 'data inspection', 'basic cleaning'],
                'code_examples': [
                    '# Reading CSV files\ndata <- read.csv("file.csv", header = TRUE)\nstr(data)\nhead(data)',
                    '# Basic data cleaning\ndata$column <- as.factor(data$column)\ndata <- na.omit(data)'
                ],
                'packages': ['base', 'utils'],
                'learning_objectives': [
                    'Importing data from files',
                    'Inspecting data structure',
                    'Basic data cleaning techniques'
                ]
            }
        }
    },
    'premium_topics': {
        'advanced ggplot2': {
            'intermediate': {
                'concepts': ['grammar of graphics', 'layered approach', 'themes'],
                'code_examples': [
                    '# Advanced ggplot\nlibrary(ggplot2)\nggplot(data, aes(x=var1, y=var2)) +\n  geom_point(aes(color=factor(group))) +\n  theme_minimal() +\n  labs(title="Advanced Visualization")'
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
                    '# Custom theme and faceting\nlibrary(ggplot2)\nlibrary(gganimate)\nplot <- ggplot(data) + \n  geom_point() + \n  facet_wrap(~category) +\n  theme_custom() +\n  transition_reveal(time)'
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
                    '# Basic ML workflow\nlibrary(caret)\nset.seed(123)\nmodel <- train(target ~ ., data=train_data, method="rf", trControl=trainControl(method="cv"))\npredictions <- predict(model, test_data)'
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
                    '# Advanced ML pipeline\nlibrary(tidymodels)\nlibrary(ranger)\nrf_spec <- rand_forest(trees = 1000, mtry = tune()) %>%\n  set_engine("ranger") %>%\n  set_mode("regression")\n\nworkflow <- workflow() %>%\n  add_model(rf_spec) %>%\n  add_formula(target ~ .)'
                ],
                'packages': ['tidymodels', 'ranger', 'xgboost', 'glmnet'],
                'learning_objectives': [
                    'Advanced ML algorithms implementation',
                    'Automated hyperparameter tuning',
                    'Building production ML pipelines'
                ]
            }
        },
        'shiny dashboards': {
            'intermediate': {
                'concepts': ['reactive programming', 'UI layouts', 'server logic'],
                'code_examples': [
                    '# Shiny app structure\nlibrary(shiny)\nui <- fluidPage(\n  titlePanel("My Dashboard"),\n  sidebarLayout(\n    sidebarPanel(\n      selectInput("variable", "Choose:", choices = names(data))\n    ),\n    mainPanel(\n      plotOutput("plot")\n    )\n  )\n)\n\nserver <- function(input, output) {\n  output$plot <- renderPlot({\n    hist(data[[input$variable]])\n  })\n}'
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
                    '# Shiny modules\nlibrary(shiny)\n\n# Module UI\nplotModuleUI <- function(id) {\n  ns <- NS(id)\n  tagList(\n    selectInput(ns("type"), "Plot type:", choices = c("histogram", "boxplot")),\n    plotOutput(ns("plot"))\n  )\n}\n\n# Module Server\nplotModuleServer <- function(id, data) {\n  moduleServer(id, function(input, output, session) {\n    output$plot <- renderPlot({\n      if(input$type == "histogram") {\n        hist(data())\n      } else {\n        boxplot(data())\n      }\n    })\n  })\n}'
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
            'intermediate': {
                'concepts': ['linear models', 'model diagnostics', 'model selection'],
                'code_examples': [
                    '# Linear modeling\nlibrary(broom)\nmodel <- lm(response ~ predictor1 + predictor2, data = data)\nsummary(model)\n\n# Model diagnostics\npar(mfrow = c(2, 2))\nplot(model)\n\n# Model comparison\nmodel2 <- lm(response ~ predictor1, data = data)\nanova(model, model2)'
                ],
                'packages': ['stats', 'broom', 'car'],
                'learning_objectives': [
                    'Building and interpreting linear models',
                    'Model diagnostic techniques',
                    'Model selection and comparison'
                ]
            },
            'expert': {
                'concepts': ['mixed effects models', 'generalized linear models', 'survival analysis'],
                'code_examples': [
                    '# Mixed effects modeling\nlibrary(lme4)\nlibrary(broom.mixed)\nmodel <- lmer(response ~ fixed_effect + (1|random_effect), data=data)\nsummary(model)\ntidy(model)\n\n# Generalized linear model\nglm_model <- glm(binary_outcome ~ predictor, family = binomial, data = data)\nsummary(glm_model)'
                ],
                'packages': ['lme4', 'nlme', 'broom', 'broom.mixed', 'survival'],
                'learning_objectives': [
                    'Advanced statistical modeling techniques',
                    'Mixed effects models',
                    'Generalized linear models',
                    'Model diagnostics and validation'
                ]
            }
        },
        'data wrangling': {
            'intermediate': {
                'concepts': ['dplyr operations', 'data reshaping', 'string manipulation'],
                'code_examples': [
                    '# Advanced data wrangling\nlibrary(dplyr)\nlibrary(tidyr)\nlibrary(stringr)\n\ndata %>%\n  filter(condition) %>%\n  group_by(category) %>%\n  summarise(\n    mean_value = mean(value, na.rm = TRUE),\n    count = n()\n  ) %>%\n  arrange(desc(mean_value))\n\n# Data reshaping\nwide_data <- data %>%\n  pivot_wider(names_from = category, values_from = value)'
                ],
                'packages': ['dplyr', 'tidyr', 'stringr', 'lubridate'],
                'learning_objectives': [
                    'Advanced data manipulation with dplyr',
                    'Data reshaping techniques',
                    'String and date manipulation'
                ]
            },
            'expert': {
                'concepts': ['complex joins', 'nested data', 'functional programming'],
                'code_examples': [
                    '# Complex data operations\nlibrary(purrr)\nlibrary(dplyr)\n\n# Nested data and list-columns\nnested_data <- data %>%\n  group_by(category) %>%\n  nest() %>%\n  mutate(\n    model = map(data, ~ lm(y ~ x, data = .x)),\n    predictions = map2(model, data, ~ predict(.x, newdata = .y))\n  )\n\n# Complex joins\nresult <- data1 %>%\n  left_join(data2, by = c("id" = "foreign_id")) %>%\n  anti_join(data3, by = "id")'
                ],
                'packages': ['dplyr', 'purrr', 'tidyr', 'broom'],
                'learning_objectives': [
                    'Complex data joining strategies',
                    'Working with nested data structures',
                    'Functional programming with purrr'
                ]
            }
        },
        'package development': {
            'expert': {
                'concepts': ['package structure', 'documentation', 'testing'],
                'code_examples': [
                    '# Package development basics\nlibrary(devtools)\nlibrary(roxygen2)\n\n# Create package structure\ncreate_package("mypackage")\n\n# Document functions\n#\' Add two numbers\n#\'\n#\' @param x A number\n#\' @param y A number\n#\' @return The sum of x and y\n#\' @export\nadd_numbers <- function(x, y) {\n  x + y\n}\n\n# Generate documentation\ndocument()\n\n# Run tests\ntest()'
                ],
                'packages': ['devtools', 'roxygen2', 'testthat', 'usethis'],
                'learning_objectives': [
                    'Creating R packages',
                    'Writing comprehensive documentation',
                    'Implementing unit tests',
                    'Package distribution and maintenance'
                ]
            }
        }
    }
}

# Email templates for notifications (future feature)
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to R Tutor Pro!',
        'template': 'emails/welcome.html'
    },
    'usage_limit_warning': {
        'subject': 'You\'re approaching your monthly tutorial limit',
        'template': 'emails/usage_warning.html'
    },
    'plan_upgraded': {
        'subject': 'Your R Tutor Pro plan has been upgraded!',
        'template': 'emails/plan_upgraded.html'
    },
    'tutorial_ready': {
        'subject': 'Your R tutorial is ready!',
        'template': 'emails/tutorial_ready.html'
    }
}

# AI Service Configuration
AI_CONFIG = {
    'deepseek': {
        'base_url': 'https://api.deepseek.com/v1/chat/completions',
        'model': 'deepseek-chat',
        'max_tokens': 2000,
        'temperature': 0.7,
        'timeout': 30
    },
    'openai': {
        'base_url': 'https://api.openai.com/v1/chat/completions',
        'model': 'gpt-3.5-turbo',
        'max_tokens': 2000,
        'temperature': 0.7,
        'timeout': 30
    }
}

# Analytics and Tracking Configuration
ANALYTICS_CONFIG = {
    'track_tutorial_generation': True,
    'track_user_interactions': True,
    'track_error_events': True,
    'retention_days': 90,  # How long to keep analytics data
    'batch_size': 100,     # For bulk operations
    'export_formats': ['json', 'csv']
}

# Security Configuration
SECURITY_CONFIG = {
    'max_login_attempts': 5,
    'login_attempt_window': 15,  # minutes
    'password_reset_token_expiry': 24,  # hours
    'api_key_expiry_days': 365,
    'session_timeout': 24,  # hours
    'allowed_file_types': ['txt', 'csv', 'json'],
    'max_file_size': 10 * 1024 * 1024,  # 10MB
}

# Tutorial Generation Limits
TUTORIAL_LIMITS = {
    'free': {
        'max_duration': 5,
        'max_topics_per_day': 3,
        'allowed_expertise_levels': ['beginner'],
        'premium_content': False
    },
    'pro': {
        'max_duration': 60,
        'max_topics_per_day': 50,
        'allowed_expertise_levels': ['beginner', 'intermediate', 'expert'],
        'premium_content': True
    },
    'team': {
        'max_duration': 60,
        'max_topics_per_day': 200,
        'allowed_expertise_levels': ['beginner', 'intermediate', 'expert'],
        'premium_content': True
    }
}

# Feature Flags
FEATURE_FLAGS = {
    'audio_generation': False,      # Coming soon
    'team_management': False,       # Coming soon
    'api_access': True,            # Available for team plan
    'export_options': True,        # Available for pro+ plans
    'analytics_dashboard': True,   # Available for all plans
    'custom_themes': False,        # Future feature
    'collaborative_editing': False, # Future feature
    'offline_mode': False          # Future feature
}

# Default User Settings
DEFAULT_USER_SETTINGS = {
    'expertise_level': 'beginner',
    'tutorial_duration': 5,
    'notification_preferences': {
        'email_notifications': True,
        'tutorial_reminders': True,
        'usage_warnings': True,
        'feature_updates': True
    },
    'privacy_settings': {
        'analytics_tracking': True,
        'usage_statistics': True,
        'performance_monitoring': True
    }
}

# Application Metadata
APP_METADATA = {
    'name': 'R Tutor Pro',
    'version': '1.0.0',
    'description': 'AI-Powered R Programming Learning Platform',
    'author': 'R Tutor Pro Team',
    'license': 'Proprietary',
    'support_email': 'support@rtutorpro.com',
    'website': 'https://rtutorpro.com',
    'documentation': 'https://docs.rtutorpro.com'
}

# Environment-specific overrides
def get_config(env=None):
    """Get configuration based on environment"""
    env = env or os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# Validation functions
def validate_plan(plan_name):
    """Validate if plan exists"""
    return plan_name in PLANS

def get_plan_limits(plan_name):
    """Get limits for a specific plan"""
    if not validate_plan(plan_name):
        return TUTORIAL_LIMITS['free']
    return TUTORIAL_LIMITS.get(plan_name, TUTORIAL_LIMITS['free'])

def get_plan_features(plan_name):
    """Get features for a specific plan"""
    if not validate_plan(plan_name):
        return PLANS['free']['features']
    return PLANS.get(plan_name, PLANS['free'])['features']

# Helper function to check if feature is enabled
def is_feature_enabled(feature_name):
    """Check if a feature flag is enabled"""
    return FEATURE_FLAGS.get(feature_name, False)

# Database URI validation and setup
def setup_database_uri():
    """Setup and validate database URI"""
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Handle Heroku postgres:// URLs
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Default to SQLite for development
    return 'sqlite:///r_tutor_pro.db'

# Initialize configuration based on environment
def init_config():
    """Initialize configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = get_config(env)
    
    # Override database URI if needed
    if not hasattr(config_class, 'SQLALCHEMY_DATABASE_URI') or not config_class.SQLALCHEMY_DATABASE_URI:
        config_class.SQLALCHEMY_DATABASE_URI = setup_database_uri()
    
    return config_class