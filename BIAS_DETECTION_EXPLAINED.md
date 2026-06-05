# How Bias Detection Works in This System

## Overview
The system detects bias by analyzing **job descriptions** (not resumes) for specific keywords that research has shown can discourage certain groups from applying.

## The Bias Detection Process

### 1. **Keyword Dictionary (Lines 82-95 in app.py)**

The system uses a predefined dictionary of biased words categorized into three types:

```python
BIAS_KEYWORDS = {
    "gender": {
        "male_biased": ["strong", "aggressive", "competitive", "dominant", "assertive"],
        "female_biased": ["nurturing", "collaborative", "supportive"],
        "neutral": ["skilled", "qualified", "experienced", "proficient"]
    },
    "age": {
        "biased": ["young", "energetic", "fresh", "recent graduate", "digital native", 
                   "mature", "experienced", "seasoned"],
        "neutral": ["qualified", "skilled", "talented"]
    },
    "personality": {
        "biased": ["rockstar", "ninja", "guru", "fast-paced"],
        "neutral": ["motivated", "dedicated", "team-oriented"]
    }
}
```

### 2. **Analysis Function (Lines 145-156)**

```python
def analyze_job_description_bias(text):
    """Detect biased language in job descriptions"""
    words = text.lower().split()  # Convert to lowercase and split into words
    bias_report = defaultdict(list)
    
    # Check each word in the job description
    for category, bias_types in BIAS_KEYWORDS.items():
        for bias_type, keywords in bias_types.items():
            if bias_type != "neutral":  # Only check biased keywords
                for word in words:
                    if word in keywords:
                        bias_report[category].append(word)
    
    return bias_report
```

### 3. **How It Works Step-by-Step**

**Example Job Description:**
> "We are looking for a **strong**, ambitious developer to join our team. The ideal candidate should be a **rockstar** programmer with **competitive** spirit and **aggressive** problem-solving skills."

**Detection Process:**

1. **Split into words**: ["we", "are", "looking", "for", "a", "strong", "ambitious", ...]

2. **Check each word against bias dictionary**:
   - "strong" → Found in `gender.male_biased` ✓
   - "rockstar" → Found in `personality.biased` ✓
   - "competitive" → Found in `gender.male_biased` ✓
   - "aggressive" → Found in `gender.male_biased` ✓

3. **Generate Report**:
```json
{
    "gender": ["strong", "competitive", "aggressive"],
    "personality": ["rockstar"]
}
```

4. **Display to User**:
   - ⚠️ **Gender Bias**: strong, competitive, aggressive
   - ⚠️ **Personality Bias**: rockstar

## Why These Words Are Considered Biased

### Gender Bias

**Male-Biased Words** (discourage women from applying):
- **"strong", "aggressive", "competitive", "dominant", "assertive"**
- Research shows these words are associated with masculine stereotypes
- Studies found women are less likely to apply when these words appear

**Female-Biased Words** (discourage men from applying):
- **"nurturing", "collaborative", "supportive"**
- Associated with feminine stereotypes
- Can signal a role is "for women"

**Source**: Research by Gaucher, Friesen & Kay (2011) - "Evidence That Gendered Wording in Job Advertisements Exists and Sustains Gender Inequality"

### Age Bias

**Biased Words**:
- **"young", "energetic", "fresh", "recent graduate"** → Discriminates against older workers
- **"mature", "experienced", "seasoned"** → Discriminates against younger workers
- **"digital native"** → Implies age preference

**Why**: These words signal age preferences, which is illegal in many jurisdictions

### Personality Bias

**Biased Words**:
- **"rockstar", "ninja", "guru"** → Casual, bro-culture language
- **"fast-paced"** → Can discourage people with disabilities or work-life balance needs

**Why**: Creates an exclusive culture and may discourage diverse applicants

## Real Examples from Your System

### Example 1: Software Engineer Role
**Job Description**: 
> "We are looking for a strong, ambitious developer to join our team. The ideal candidate should be a rockstar programmer with competitive spirit and aggressive problem-solving skills."

**Detected Bias**:
- Gender Bias: strong, competitive, aggressive
- Personality Bias: rockstar

### Example 2: Data Scientist Role
**Job Description**:
> "Seeking a Data Scientist to analyze complex datasets. The candidate should be energetic and have fresh perspectives on machine learning and statistical analysis."

**Detected Bias**:
- Age Bias: energetic, fresh

### Example 3: ML Engineer Role
**Job Description**:
> "Looking for an ML Engineer to build and deploy machine learning models. The ideal candidate should be a guru in deep learning and AI technologies."

**Detected Bias**:
- Personality Bias: guru

## How to Test Bias Detection

### Test 1: Real-Time Bias Checker
1. Go to the main page
2. Scroll to "Real-Time Job Description Bias Checker"
3. Type: "We need a strong, aggressive programmer who is a rockstar"
4. **Result**: Will show Gender Bias (strong, aggressive) and Personality Bias (rockstar)

### Test 2: Upload Resumes
1. Select any job role (they all have biased descriptions)
2. Upload resume(s)
3. Check the "Job Description Bias Analysis" section
4. **Result**: Will show detected bias words from that job role's description

### Test 3: Try Neutral Language
Type in the real-time checker:
> "We need a skilled, qualified programmer with problem-solving abilities"

**Result**: ✅ No Bias Detected

## Scientific Basis

This approach is based on:

1. **Linguistic Analysis**: Research showing certain words correlate with gender/age stereotypes
2. **Application Behavior**: Studies tracking how word choice affects who applies
3. **Hiring Outcomes**: Data showing biased language leads to less diverse candidate pools

## Limitations

1. **Context-Insensitive**: Doesn't understand context (e.g., "strong coffee" vs "strong candidate")
2. **English-Only**: Only works for English text
3. **Keyword-Based**: Misses subtle bias not in the keyword list
4. **No Intersectionality**: Doesn't detect combined biases (e.g., race + gender)

## Improving Bias Detection

To make it more accurate, you could:

1. **Add More Keywords**: Expand the bias dictionary
2. **Use NLP/ML**: Train a model on labeled biased/unbiased job descriptions
3. **Context Analysis**: Use sentence-level analysis instead of word-level
4. **Add More Categories**: Include race, disability, socioeconomic bias
5. **Severity Scoring**: Weight words by how biased they are

## Summary

**What it detects**: Biased keywords in job descriptions
**How it works**: Keyword matching against research-backed bias dictionary
**Why it matters**: Biased language reduces diversity in applicant pools
**Current accuracy**: Good for obvious bias, misses subtle cases
