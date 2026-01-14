import os
import json
import time
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TrainingDataSynthesizer:
    def __init__(self, input_dir='svvsd_pages', output_dir='svvsd_training_data'):
        """
        Initialize the synthesizer
        
        Args:
            input_dir: Directory containing scraped text files
            output_dir: Directory for synthesized training data
        """
        self.input_dir = input_dir
        self.output_dir = output_dir

        with open("src/Training/SynthesizerPrompt.md", 'r', encoding='utf-8') as file:
            self.prompt = file.read() 
        
        # Get API key from .env file
        api_key = os.getenv('DEEPINFRA_API_KEY')
        if not api_key:
            raise ValueError("DEEPINFRA_API_KEY not found in .env file")
        
        # Initialize OpenAI client with DeepInfra configuration
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepinfra.com/v1/openai"
        )
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
    def read_file(self, filepath):
        """Read content from a file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def create_synthesis_prompt(self, content):
        """Create a prompt for the LLM to synthesize training data"""
        prompt = f"""You are an expert at creating high-quality training data for language models. 

I have scraped content from the St. Vrain Valley School District (SVVSD) website. Your task is to synthesize this information into well-organized training data that will help a language model understand and answer questions about SVVSD.

Original Content:
{content}

Please create comprehensive training data with the following sections:

## Summary
A clear, concise summary of the main information (2-3 paragraphs)

## Key Facts
Extract 5-10 important facts as bullet points

## Question-Answer Pairs
Generate 5-8 diverse question-answer pairs that could be asked about this content. Include:
- Factual questions (who, what, when, where)
- Explanatory questions (how, why)
- Practical questions (how do I, what should I)

Format as:
**Q:** [question]
**A:** [answer]

## Entities
List important entities mentioned (people, places, programs, departments, dates)

## Topics/Categories
Identify the main topics this content covers (e.g., enrollment, curriculum, events, policies)

## Contextual Information
Any additional context that would help someone understand this information better

Please format your response in clear Markdown with proper headers and structure."""
        
        return prompt
    
    def synthesize_content(self, content, filename):
        """Use DeepInfra KimiK2 to synthesize training data"""
        try:
            print(f"  → Synthesizing: {filename}")
            
            prompt = self.create_synthesis_prompt(content)
            
            response = self.client.chat.completions.create(
                model="moonshotai/Kimi-K2-Thinking",  # KimiK2 thinking model
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000  # KimiK2 can handle longer responses
            )
            
            # Extract the response (already in markdown format)
            synthesis = response.choices[0].message.content
            
            print(f"  ✓ Synthesized successfully")
            return synthesis
            
        except Exception as e:
            print(f"  ✗ Error synthesizing {filename}: {str(e)}")
            return None
    
    def process_all_files(self, delay=1):
        """Process all files in the input directory"""
        # Get all text files except the index
        files = [f for f in os.listdir(self.input_dir) 
                if f.endswith('.txt') and not f.startswith('000_INDEX')]
        
        files.sort()  # Process in order
        
        print(f"\nFound {len(files)} files to process")
        print(f"Output directory: {self.output_dir}\n")
        
        results = []
        
        for idx, filename in enumerate(files, 1):
            print(f"[{idx}/{len(files)}] Processing: {filename}")
            
            # Read original content
            filepath = os.path.join(self.input_dir, filename)
            content = self.read_file(filepath)
            
            # Skip if file is too short (likely not useful)
            if len(content) < 200:
                print(f"  ⊘ Skipping (too short)")
                continue
            
            # Synthesize with LLM
            synthesis = self.synthesize_content(content, filename)
            
            if synthesis:
                # Create individual output file for this synthesis
                base_name = filename.replace('.txt', '')
                output_file = os.path.join(self.output_dir, f"{base_name}_synthesized.md")
                
                # Create markdown content
                markdown_content = f"""# Synthesized Training Data
**Source File:** {filename}
**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

## Original Content

{content}

---

## Synthesized Analysis

{synthesis}
"""
                
                # Save to individual markdown file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)
                
                # Store for master file creation
                results.append({
                    'filename': filename,
                    'original_content': content,
                    'synthesized_data': synthesis,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
                print(f"  ✓ Saved to: {output_file}\n")
            
            # Delay to respect API rate limits
            time.sleep(delay)
        
        return results
    
    def create_master_training_file(self, results):
        """Create master training files in various formats"""
        
        # 1. Complete Markdown with all synthesized data
        master_md = os.path.join(self.output_dir, 'master_training_data.md')
        with open(master_md, 'w', encoding='utf-8') as f:
            f.write("# SVVSD Master Training Data\n\n")
            f.write(f"**Total Pages Processed:** {len(results)}\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            for idx, result in enumerate(results, 1):
                f.write(f"# Page {idx}: {result['filename']}\n\n")
                f.write(result['synthesized_data'])
                f.write("\n\n---\n\n")
        
        print(f"✓ Created master Markdown: {master_md}")
        
        # 2. JSON backup for programmatic access
        master_json = os.path.join(self.output_dir, 'master_training_data.json')
        with open(master_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Created master JSON backup: {master_json}")
        
        # 3. Combined text format (simple training format)
        text_path = os.path.join(self.output_dir, 'combined_training_text.txt')
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write("SVVSD TRAINING DATA - COMBINED TEXT FORMAT\n")
            f.write("=" * 80 + "\n\n")
            
            for result in results:
                f.write("=" * 80 + "\n")
                f.write(f"SOURCE: {result['filename']}\n")
                f.write("=" * 80 + "\n\n")
                f.write(result['synthesized_data'])
                f.write("\n\n" + "=" * 80 + "\n\n")
        
        print(f"✓ Created combined text: {text_path}")
        
        # 4. Create statistics file
        stats_path = os.path.join(self.output_dir, 'statistics.md')
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write("# Training Data Statistics\n\n")
            f.write(f"**Total files processed:** {len(results)}\n")
            f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Processed Files\n\n")
            for idx, result in enumerate(results, 1):
                f.write(f"{idx}. `{result['filename']}`\n")
            
            f.write(f"\n**Output Directory:** `{self.output_dir}/`\n")
        
        print(f"✓ Created statistics: {stats_path}")


# Example usage
if __name__ == "__main__":
    # API key is automatically loaded from .env file
    # Make sure your .env file contains: DEEPINFRA_API_KEY=your_key_here
    
    synthesizer = TrainingDataSynthesizer(
        input_dir='svvsd_pages',
        output_dir='svvsd_training_data'
    )
    
    print("=" * 80)
    print("SVVSD Training Data Synthesizer")
    print("Using: DeepInfra - Kimi/k2-thinking")
    print("=" * 80)
    
    # Process all files
    results = synthesizer.process_all_files(delay=1)
    
    # Create master training files
    print("\n" + "=" * 80)
    print("Creating Master Training Files")
    print("=" * 80 + "\n")
    synthesizer.create_master_training_file(results)
    
    print("\n" + "=" * 80)
    print(f"✓ ALL DONE! Processed {len(results)} files")
    print(f"✓ Output saved to: {synthesizer.output_dir}/")
    print("=" * 80)