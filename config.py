# config.py - Modified to remove premium restrictions
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

# Simplified Plans Configuration - All features free
PLANS = {
    'free': {
        'tutorials_per_month': 999,  # Essentially unlimited
        'price': 0,
        'stripe_price_id': None,
        'features': [
            'Unlimited R tutorials',
            'All R topics including advanced',
            'AI-generated premium content',
            'Up to 60-minute tutorials',
            'All packages and concepts',
            'Community support',
            'Web access'
        ],
        'limits': {
            'max_duration': 60,
            'audio_generation': True,  # Enable for all users
            'premium_topics': True,    # Enable for all users
            'api_access': True,        # Enable for all users
            'export_options': True     # Enable for all users
        }
    }
}

# All R Content Available to Everyone
R_TOPICS_CONTENT = {
    'all_topics': {  # Single category containing all content
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
        'ggplot2 visualization': {
            'beginner': {
                'concepts': ['grammar of graphics', 'basic plots', 'aesthetics'],
                'code_examples': [
                    '# Basic ggplot\nlibrary(ggplot2)\nggplot(data, aes(x=var1, y=var2)) +\n  geom_point() +\n  theme_minimal()'
                ],
                'packages': ['ggplot2', 'scales'],
                'learning_objectives': [
                    'Understanding ggplot2 syntax',
                    'Creating basic visualizations',
                    'Customizing plot appearance'
                ]
            },
            'intermediate': {
                'concepts': ['layered approach', 'faceting', 'themes'],
                'code_examples': [
                    '# Advanced ggplot with faceting\nggplot(data, aes(x=var1, y=var2)) +\n  geom_point(aes(color=factor(group))) +\n  facet_wrap(~category) +\n  theme_minimal()'
                ],
                'packages': ['ggplot2', 'scales', 'RColorBrewer'],
                'learning_objectives': [
                    'Advanced visualization techniques',
                    'Creating multi-panel plots',
                    'Custom themes and styling'
                ]
            },
            'expert': {
                'concepts': ['custom themes', 'complex layouts', 'animations'],
                'code_examples': [
                    '# Custom theme and complex layout\nlibrary(ggplot2)\nlibrary(patchwork)\np1 <- ggplot(data) + geom_point()\np2 <- ggplot(data) + geom_bar(stat="identity")\n(p1 | p2) / p3'
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

# Simplified Tutorial Limits - No restrictions
TUTORIAL_LIMITS = {
    'free': {
        'max_duration': 60,
        'max_topics_per_day': 999,
        'allowed_expertise_levels': ['beginner', 'intermediate', 'expert'],
        'premium_content': True
    }
}

# Feature Flags - All enabled
FEATURE_FLAGS = {
    'audio_generation': True,
    'team_management': True,
    'api_access': True,
    'export_options': True,
    'analytics_dashboard': True,
    'custom_themes': True,
    'collaborative_editing': True,
    'offline_mode': False
}

# Helper functions
def validate_plan(plan_name):
    """Validate if plan exists"""
    return plan_name == 'free'  # Only free plan exists now

def get_plan_limits(plan_name):
    """Get limits for a specific plan"""
    return TUTORIAL_LIMITS['free']  # Everyone gets full access

def get_plan_features(plan_name):
    """Get features for a specific plan"""
    return PLANS['free']['features']  # Everyone gets all features

def is_feature_enabled(feature_name):
    """Check if a feature flag is enabled"""
    return FEATURE_FLAGS.get(feature_name, True)  # Default to enabled