from google import genai
from google.genai import types
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)


class CVOutput(BaseModel):
    latex_code: str


def generate_cv_with_gemini(user_data, job_description, template_name):
    """
    Generate CV LaTeX code using Gemini AI.
    
    Args:
        user_data (dict): User information and details
        job_description (str): Job description to tailor CV for
        template_name (str): Template name to use
        
    Returns:
        str: Generated LaTeX code
    """
    try:
        # Configure Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        client = genai.Client(api_key=api_key)
        
        # Load template
        template_content = load_template(template_name)
        
        # Create comprehensive prompt
        prompt = f"""
You are a professional CV writer with expertise in creating compelling resumes that get interviews.

Create a professional CV based on the following information:

USER INFORMATION:
{format_user_data(user_data)}

JOB DESCRIPTION TO TAILOR FOR:
{job_description}

LATEX TEMPLATE TO CUSTOMIZE:
{template_content}

INSTRUCTIONS:
1. Customize the CV content to match the job requirements perfectly
2. Highlight relevant skills, experiences, and achievements
3. Use action verbs and quantify achievements where possible
4. Ensure the content flows naturally and professionally
5. Optimize for ATS (Applicant Tracking Systems)
6. Keep the LaTeX formatting intact and valid
7. Replace all placeholder content with the user's actual information
8. Tailor the professional summary to match the job requirements
9. Prioritize relevant experience and skills
10. Use industry-specific keywords from the job description

OUTPUT REQUIREMENTS:
- Return only valid LaTeX code that can be compiled
- Ensure all LaTeX syntax is correct
- No explanations or additional text outside the LaTeX code
- Make sure all special characters are properly escaped

Provide the complete LaTeX code in the latex_code field.
"""
        
        # Generate content with structured output
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CVOutput,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        # Use the parsed response
        cv_output: CVOutput = response.parsed
        latex_code = cv_output.latex_code
        
        # Validate the generated LaTeX
        if not latex_code or len(latex_code.strip()) < 100:
            raise Exception("Generated LaTeX code is too short or empty")
        
        if not latex_code.strip().startswith('\\documentclass'):
            raise Exception("Generated code doesn't appear to be valid LaTeX")
        
        logger.info(f"Successfully generated CV with Gemini for template {template_name}")
        return latex_code
        
    except Exception as e:
        logger.error(f"Failed to generate CV with Gemini: {str(e)}")
        # Return fallback template with user data
        return get_fallback_template(user_data, job_description, template_name)


def edit_cv_with_gemini(existing_latex, edit_instructions, user_data, job_description):
    """
    Edit existing CV LaTeX code using Gemini AI.
    
    Args:
        existing_latex (str): Current LaTeX code
        edit_instructions (str): Instructions for editing
        user_data (dict): User information
        job_description (str): Job description context
        
    Returns:
        str: Edited LaTeX code
    """
    try:
        # Configure Gemini
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        client = genai.Client(api_key=api_key)
        
        # Create editing prompt
        prompt = f"""
You are a professional CV editor with expertise in improving resumes for better job matching.

CURRENT CV LATEX CODE:
{existing_latex}

USER INFORMATION (for context):
{format_user_data(user_data)}

JOB DESCRIPTION (for context):
{job_description}

EDITING INSTRUCTIONS:
{edit_instructions}

TASK:
Modify the existing LaTeX CV code according to the editing instructions while:

1. Maintaining the overall structure and formatting
2. Improving content quality and relevance
3. Ensuring the CV better matches the job requirements
4. Keeping all LaTeX syntax valid and compilable
5. Preserving the professional tone and readability
6. Making strategic improvements to highlight relevant skills
7. Optimizing for ATS compatibility
8. Following the specific editing instructions provided

IMPORTANT:
- Return only the complete modified LaTeX code
- Ensure all changes improve the CV's effectiveness
- Maintain proper LaTeX formatting and syntax
- Don't remove essential structural elements
- Keep the CV concise and focused

Provide the complete edited LaTeX code in the latex_code field.
"""
        
        # Generate edited content
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CVOutput,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        
        # Use the parsed response
        cv_output: CVOutput = response.parsed
        edited_latex = cv_output.latex_code
        
        # Validate the edited LaTeX
        if not edited_latex or len(edited_latex.strip()) < 100:
            raise Exception("Edited LaTeX code is too short or empty")
        
        if not edited_latex.strip().startswith('\\documentclass'):
            raise Exception("Edited code doesn't appear to be valid LaTeX")
        
        logger.info(f"Successfully edited CV with Gemini")
        return edited_latex
        
    except Exception as e:
        logger.error(f"Failed to edit CV with Gemini: {str(e)}")
        # Return original LaTeX if editing fails
        return existing_latex


def load_template(template_name):
    """
    Load LaTeX template from file.
    
    Args:
        template_name (str): Name of the template
        
    Returns:
        str: Template content
    """
    try:
        template_path = f'latex_templates/{template_name}.tex'
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            logger.warning(f"Template file not found: {template_path}")
            return get_basic_template()
            
    except Exception as e:
        logger.error(f"Error loading template {template_name}: {str(e)}")
        return get_basic_template()


def format_user_data(user_data):
    """
    Format user data for the prompt.
    
    Args:
        user_data (dict): User information
        
    Returns:
        str: Formatted user data string
    """
    try:
        formatted_lines = []
        
        # Basic information
        if user_data.get('name'):
            formatted_lines.append(f"Name: {user_data['name']}")
        if user_data.get('email'):
            formatted_lines.append(f"Email: {user_data['email']}")
        if user_data.get('phone'):
            formatted_lines.append(f"Phone: {user_data['phone']}")
        if user_data.get('location'):
            formatted_lines.append(f"Location: {user_data['location']}")
        if user_data.get('linkedin'):
            formatted_lines.append(f"LinkedIn: {user_data['linkedin']}")
        if user_data.get('website'):
            formatted_lines.append(f"Website: {user_data['website']}")
        
        # Professional summary
        if user_data.get('summary'):
            formatted_lines.append(f"\nProfessional Summary:\n{user_data['summary']}")
        
        # Experience
        if user_data.get('experience'):
            formatted_lines.append(f"\nExperience:\n{user_data['experience']}")
        
        # Skills
        if user_data.get('skills'):
            if isinstance(user_data['skills'], list):
                skills_str = ', '.join(user_data['skills'])
            else:
                skills_str = str(user_data['skills'])
            formatted_lines.append(f"\nSkills: {skills_str}")
        
        # Education
        if user_data.get('education'):
            formatted_lines.append(f"\nEducation:\n{user_data['education']}")
        
        # Projects
        if user_data.get('projects'):
            formatted_lines.append(f"\nProjects:\n{user_data['projects']}")
        
        # Certifications
        if user_data.get('certifications'):
            formatted_lines.append(f"\nCertifications:\n{user_data['certifications']}")
        
        # Languages
        if user_data.get('languages'):
            formatted_lines.append(f"\nLanguages: {user_data['languages']}")
        
        # Additional sections
        for key, value in user_data.items():
            if key not in ['name', 'email', 'phone', 'location', 'linkedin', 'website', 
                          'summary', 'experience', 'skills', 'education', 'projects', 
                          'certifications', 'languages'] and value:
                formatted_lines.append(f"\n{key.title()}: {value}")
        
        return '\n'.join(formatted_lines)
        
    except Exception as e:
        logger.error(f"Error formatting user data: {str(e)}")
        return str(user_data)


def get_basic_template():
    """
    Get basic LaTeX template as fallback.
    
    Returns:
        str: Basic LaTeX template
    """
    return r"""
\documentclass[11pt,a4paper,sans]{moderncv}
\moderncvstyle{classic}
\moderncvcolor{blue}
\usepackage[scale=0.75]{geometry}
\usepackage[utf8]{inputenc}

% Personal data
\name{[NAME]}{\space}
\title{[TITLE]}
\address{[ADDRESS]}{\space}{\space}
\phone[mobile]{[PHONE]}
\email{[EMAIL]}
\social[linkedin]{[LINKEDIN]}
\social[github]{[GITHUB]}

\begin{document}
\makecvtitle

\section{Professional Summary}
[SUMMARY]

\section{Experience}
\cventry{[YEAR]--[YEAR]}{[POSITION]}{[COMPANY]}{[LOCATION]}{}{%
[DESCRIPTION]
\begin{itemize}%
\item [ACHIEVEMENT_1]
\item [ACHIEVEMENT_2]
\item [ACHIEVEMENT_3]
\end{itemize}}

\section{Education}
\cventry{[YEAR]--[YEAR]}{[DEGREE]}{[INSTITUTION]}{[LOCATION]}{\textit{[GPA]}}{[DESCRIPTION]}

\section{Skills}
\cvitemwithcomment{Programming}{[PROGRAMMING_SKILLS]}{[LEVEL]}
\cvitemwithcomment{Technologies}{[TECH_SKILLS]}{[LEVEL]}
\cvitemwithcomment{Languages}{[LANGUAGES]}{[LEVEL]}

\section{Projects}
\cventry{[YEAR]}{[PROJECT_NAME]}{[TECH_STACK]}{}{}{%
[PROJECT_DESCRIPTION]
\begin{itemize}%
\item [FEATURE_1]
\item [FEATURE_2]
\end{itemize}}

\end{document}
"""


def get_fallback_template(user_data, job_description, template_name):
    """
    Get fallback template with basic user data substitution.
    
    Args:
        user_data (dict): User information
        job_description (str): Job description
        template_name (str): Template name
        
    Returns:
        str: LaTeX code with basic substitutions
    """
    try:
        template = get_basic_template()
        
        # Basic substitutions
        substitutions = {
            '[NAME]': user_data.get('name', 'Your Name'),
            '[TITLE]': extract_job_title(job_description) or 'Professional',
            '[EMAIL]': user_data.get('email', 'your.email@example.com'),
            '[PHONE]': user_data.get('phone', '+1-234-567-8900'),
            '[ADDRESS]': user_data.get('location', 'Your City, Country'),
            '[LINKEDIN]': user_data.get('linkedin', 'yourlinkedin'),
            '[GITHUB]': user_data.get('github', 'yourgithub'),
            '[SUMMARY]': user_data.get('summary', 'Professional with relevant experience.'),
            '[YEAR]': '2020',
            '[POSITION]': 'Position Title',
            '[COMPANY]': 'Company Name',
            '[LOCATION]': 'City, Country',
            '[DESCRIPTION]': user_data.get('experience', 'Professional experience description.'),
            '[ACHIEVEMENT_1]': 'Key achievement or responsibility',
            '[ACHIEVEMENT_2]': 'Another important accomplishment',
            '[ACHIEVEMENT_3]': 'Additional relevant experience',
            '[DEGREE]': user_data.get('education', 'Bachelor\'s Degree'),
            '[INSTITUTION]': 'University Name',
            '[GPA]': 'GPA',
            '[PROGRAMMING_SKILLS]': ', '.join(user_data.get('skills', ['Python', 'JavaScript'])) if isinstance(user_data.get('skills'), list) else str(user_data.get('skills', 'Programming Languages')),
            '[TECH_SKILLS]': 'React, Node.js, Docker',
            '[LANGUAGES]': 'English (Native), Spanish (Intermediate)',
            '[LEVEL]': 'Advanced',
            '[PROJECT_NAME]': 'Project Name',
            '[TECH_STACK]': 'Technology Stack',
            '[PROJECT_DESCRIPTION]': 'Project description and impact.',
            '[FEATURE_1]': 'Key feature or accomplishment',
            '[FEATURE_2]': 'Another important feature'
        }
        
        # Apply substitutions
        for placeholder, replacement in substitutions.items():
            template = template.replace(placeholder, replacement)
        
        logger.info(f"Generated fallback template for {template_name}")
        return template
        
    except Exception as e:
        logger.error(f"Error generating fallback template: {str(e)}")
        return get_basic_template()


def extract_job_title(job_description):
    """
    Extract job title from job description.
    
    Args:
        job_description (str): Job description text
        
    Returns:
        str: Extracted job title or None
    """
    try:
        # Simple extraction logic - look for common patterns
        job_description_lower = job_description.lower()
        
        common_titles = [
            'software engineer', 'software developer', 'full stack developer',
            'frontend developer', 'backend developer', 'data scientist',
            'product manager', 'project manager', 'marketing manager',
            'sales representative', 'business analyst', 'ux designer',
            'ui designer', 'graphic designer', 'content writer',
            'digital marketer', 'account manager', 'consultant'
        ]
        
        for title in common_titles:
            if title in job_description_lower:
                return title.title()
        
        # If no common title found, try to extract from first few words
        words = job_description.split()[:10]
        for i, word in enumerate(words):
            if word.lower() in ['engineer', 'developer', 'manager', 'analyst', 'designer', 'specialist']:
                if i > 0:
                    return ' '.join(words[max(0, i-2):i+1]).title()
                else:
                    return word.title()
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting job title: {str(e)}")
        return None


def validate_latex_code(latex_code):
    """
    Basic validation for LaTeX code.
    
    Args:
        latex_code (str): LaTeX code to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        if not latex_code or not latex_code.strip():
            return False, "LaTeX code is empty"
        
        if not latex_code.strip().startswith('\\documentclass'):
            return False, "LaTeX code must start with \\documentclass"
        
        if '\\begin{document}' not in latex_code:
            return False, "LaTeX code must contain \\begin{document}"
        
        if '\\end{document}' not in latex_code:
            return False, "LaTeX code must contain \\end{document}"
        
        # Check for balanced braces (basic check)
        open_braces = latex_code.count('{')
        close_braces = latex_code.count('}')
        
        if open_braces != close_braces:
            return False, f"Unbalanced braces: {open_braces} opening, {close_braces} closing"
        
        return True, "LaTeX code appears valid"
        
    except Exception as e:
        return False, f"Error validating LaTeX: {str(e)}"
