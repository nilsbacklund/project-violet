# OpenAI Model Update Summary

This document summarizes the changes made to support the new OpenAI o3 and o4-mini models.

## Changes Made

### 1. Model Definitions (`Red/model.py`)
- Added new model enums:
  - `O1_PREVIEW = "o1-preview"`
  - `O1_MINI = "o1-mini"`
  - `O3_MINI = "o3-mini"`
  - `O4_MINI = "o4-mini"`
- Reorganized existing models by category (legacy, current, o-series, ollama)
- Added comprehensive documentation about model characteristics and use cases

### 2. Configuration Updates (`config.py`)
- Updated primary models to use `O3_MINI` for both sangria and config generation
- Added fallback model configuration
- Added detailed documentation about model selection guidelines

### 3. API Integration Updates
Updated all OpenAI API calls across the codebase:

#### Red Team Components:
- `Red/schema.py`: Updated default model and added fallback mechanism
- `Red/defender_llm.py`: Updated to use `o3-mini`

#### Blue Team Components:
- `Blue/attack_pattern_check.py`: Updated default models
- `Blue/services.py`: Updated LLM service configurations
- `Blue/new_config_pipeline.py`: Updated documentation

#### LLM Labeler:
- `LLM_labeler/labeler.py`: Updated to use `o3-mini`
- `LLM_labeler/labeler_v2.py`: Updated API format and model

### 4. Enhanced Error Handling
- Added `response_openai_with_fallback()` function in `schema.py`
- Automatic fallback to `gpt-4o-mini` if newer models are unavailable
- Graceful degradation for model compatibility

### 5. Testing Infrastructure
- Created `test_new_models.py` for validating model functionality
- Updated `debug_messages.py` to use new models

## Model Selection Guidelines

### O3-MINI (Recommended Primary)
- **Best for**: Complex reasoning tasks, attack planning, configuration generation
- **Use cases**: Cybersecurity analysis, multi-step reasoning, structured output
- **Characteristics**: Enhanced reasoning capabilities, cost-efficient

### O4-MINI (Alternative)
- **Best for**: Speed-optimized operations, cost-sensitive applications
- **Use cases**: Simple command generation, quick responses
- **Characteristics**: Latest generation, optimized performance

### Fallback Strategy
- All new model calls automatically fall back to `gpt-4o-mini` if unavailable
- Maintains backward compatibility
- Ensures system reliability during model transitions

## Migration Notes

1. **Existing Code**: No breaking changes - existing code continues to work
2. **New Features**: Enhanced reasoning capabilities with o3/o4 models
3. **Cost Impact**: Monitor usage as new models may have different pricing
4. **Rate Limits**: New models may have different rate limit structures

## Testing

Run the test script to verify model functionality:
```bash
python test_new_models.py
```

## Configuration

To switch between models, update `config.py`:
```python
# For maximum reasoning capability
llm_model_sangria = LLMModel.O3_MINI

# For cost optimization  
llm_model_sangria = LLMModel.O4_MINI

# For compatibility (fallback)
llm_model_sangria = LLMModel.GPT_4O_MINI
```

## Rollback Plan

If issues arise with new models:
1. Update `config.py` to use `LLMModel.GPT_4O_MINI`
2. All fallback mechanisms will automatically engage
3. System returns to previous stable state

## Next Steps

1. Monitor model performance and costs
2. Fine-tune prompts for optimal o3/o4 model performance
3. Evaluate reasoning improvements in cybersecurity scenarios
4. Consider model-specific optimizations based on usage patterns
