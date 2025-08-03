TTS_OPTIONS = {
    'local_tts': {
        'enabled': True
    }
}

R_TOPICS_CONTENT = {
    'data structures': {
        'beginner': {
            'concepts': ['vectors', 'lists', 'data frames', 'matrices', 'factors'],
            'code_examples': [
                '# Creating vectors\nnumeric_vector <- c(1, 2, 3, 4, 5)\ncharacter_vector <- c("R", "is", "awesome")',
                '# Creating data frames\ndf <- data.frame(\n  name = c("Alice", "Bob", "Charlie"),\n  age = c(25, 30, 35),\n  city = c("NYC", "LA", "Chicago")\n)',
                '# Accessing elements\ndf$name  # Access column\ndf[1, ]  # Access first row\ndf[df$age > 25, ]  # Conditional selection'
            ],
            'packages': ['base', 'utils'],
            'learning_objectives': [
                'Understanding R\'s fundamental data types',
                'Creating and manipulating vectors',
                'Working with data frames effectively',
                'Basic indexing and subsetting techniques'
            ]
        },
        # ... rest of the R_TOPICS_CONTENT
    },
    # ... other topics
}
