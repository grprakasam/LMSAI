from flask import Flask, render_template, request, jsonify
import os
import random
import time

app = Flask(__name__)

# R-specific content templates
R_TOPICS_CONTENT = {
    'data structures': {
        'beginner': {
            'concepts': ['vectors', 'lists', 'data frames', 'matrices'],
            'code_examples': [
                '# Creating vectors\nnumeric_vector <- c(1, 2, 3, 4, 5)\ncharacter_vector <- c("a", "b", "c")',
                '# Creating data frames\ndf <- data.frame(name = c("Alice", "Bob"), age = c(25, 30))',
                '# Accessing elements\ndf$name  # Access column\ndf[1, ]  # Access first row'
            ]
        },
        'intermediate': {
            'concepts': ['advanced indexing', 'data manipulation', 'merging datasets'],
            'code_examples': [
                '# Advanced indexing\ndf[df$age > 25, ]\nsubset(df, age > 25 & name == "Alice")',
                '# Using dplyr for data manipulation\nlibrary(dplyr)\ndf %>% filter(age > 25) %>% select(name)'
            ]
        },
        'expert': {
            'concepts': ['memory optimization', 'custom data structures', 'S3/S4 classes'],
            'code_examples': [
                '# Creating S3 class\nsetClass("Person", slots = list(name = "character", age = "numeric"))',
                '# Memory-efficient operations\ndata.table::fread("large_file.csv")  # Fast reading'
            ]
        }
    },
    'ggplot2': {
        'beginner': {
            'concepts': ['basic plots', 'aesthetics', 'geoms'],
            'code_examples': [
                'library(ggplot2)\nggplot(mtcars, aes(x = mpg, y = hp)) + geom_point()',
                'ggplot(iris, aes(x = Species, y = Sepal.Length)) + geom_boxplot()'
            ]
        },
        'intermediate': {
            'concepts': ['faceting', 'themes', 'scales'],
            'code_examples': [
                'ggplot(mtcars, aes(x = mpg, y = hp)) + geom_point() + facet_wrap(~cyl)',
                'ggplot(iris, aes(x = Sepal.Length, fill = Species)) + geom_histogram() + theme_minimal()'
            ]
        },
        'expert': {
            'concepts': ['custom themes', 'extensions', 'complex visualizations'],
            'code_examples': [
                '# Custom theme\nmy_theme <- theme_minimal() + theme(axis.text = element_text(size = 12))',
                '# Complex multi-layer plot\nggplot(data) + geom_point() + geom_smooth() + coord_polar()'
            ]
        }
    }
}

def generate_r_content(topic, expertise, duration):
    """Generate R-specific tutorial content based on parameters"""
    
    # Simulate processing time
    time.sleep(1)
    
    # Find matching content
    topic_key = None
    for key in R_TOPICS_CONTENT.keys():
        if key.lower() in topic.lower():
            topic_key = key
            break
    
    if topic_key and expertise in R_TOPICS_CONTENT[topic_key]:
        content_data = R_TOPICS_CONTENT[topic_key][expertise]
        concepts = content_data['concepts']
        examples = content_data['code_examples']
        
        # Generate content based on duration
        if int(duration) <= 3:
            selected_concepts = concepts[:2]
            selected_examples = examples[:1]
        elif int(duration) <= 6:
            selected_concepts = concepts[:3]
            selected_examples = examples[:2]
        else:
            selected_concepts = concepts
            selected_examples = examples
        
        content = f"""
        🎯 R Tutorial: {topic.title()}
        
        📚 Key Concepts for {expertise.title()} Level:
        {', '.join(selected_concepts)}
        
        💻 Code Examples:
        {chr(10).join(selected_examples)}
        
        ⏱️ Estimated Learning Time: {duration} minutes
        
        🔗 This tutorial covers essential {topic} concepts tailored for {expertise} R developers.
        Practice these examples in RStudio for hands-on learning!
        """
    else:
        # Generic content for topics not in our database
        content = f"""
        🎯 R Tutorial: {topic.title()}
        
        📚 Customized for {expertise.title()} Level
        
        This {duration}-minute tutorial will cover:
        • Core concepts and theory
        • Practical R code examples
        • Best practices and common pitfalls
        • Real-world applications
        
        💡 Pro Tip: Practice in RStudio and experiment with the code examples!
        """
    
    return content.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        # Get form data
        topic = request.form.get('topic', '').strip()
        expertise = request.form.get('expertise', '').strip()
        duration = request.form.get('duration', '5').strip()
        
        # Validate input
        if not topic or not expertise:
            return jsonify({
                'success': False,
                'error': 'Please fill in all required fields'
            }), 400
        
        # Generate R-specific content
        audio_content = generate_r_content(topic, expertise, duration)
        
        # Add some R-specific metadata
        r_packages = []
        if 'ggplot' in topic.lower():
            r_packages.extend(['ggplot2', 'dplyr', 'tidyr'])
        elif 'data' in topic.lower():
            r_packages.extend(['dplyr', 'data.table', 'readr'])
        elif 'shiny' in topic.lower():
            r_packages.extend(['shiny', 'shinydashboard', 'DT'])
        else:
            r_packages.extend(['base', 'utils', 'stats'])
        
        return jsonify({
            'success': True,
            'audio_content': audio_content,
            'topic': topic,
            'expertise': expertise,
            'duration': duration,
            'r_packages': r_packages,
            'estimated_lines_of_code': random.randint(10, 50),
            'difficulty_score': random.randint(1, 10)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
