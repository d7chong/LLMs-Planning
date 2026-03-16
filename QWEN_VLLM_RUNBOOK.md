# Running Qwen3 and Qwen3.5 on This Repo via Local vLLM

This repo is old and has two mostly separate benchmark stacks:

- `llm_planning_analysis`
- `plan-bench`

It also has a separate backprompting eval path inside `llm_planning_analysis`.

The repo has been patched so you can route all chat-style model calls through a local OpenAI-compatible vLLM endpoint by defining engine aliases in `OPENAI_COMPATIBLE_ENGINES`.


## 1. Start vLLM

Run one model at a time unless you have enough GPU memory for multiple servers.

Example for Qwen3:

```bash
vllm serve Qwen/Qwen3-32B --host 0.0.0.0 --port 8000
```

Example for Qwen3.5:

```bash
vllm serve Qwen/Qwen3.5-32B --host 0.0.0.0 --port 8000
```

If your exact Hugging Face model id differs, use that instead.


## 2. Define Engine Aliases

From the repo root:

```bash
cd /workspaces/LLMs-Planning
```

For Qwen3:

```bash
export OPENAI_COMPATIBLE_ENGINES='{
  "qwen3_chat": {
    "base_url": "http://localhost:8000/v1",
    "model": "Qwen/Qwen3-32B"
  }
}'
```

For Qwen3.5:

```bash
export OPENAI_COMPATIBLE_ENGINES='{
  "qwen3.5_chat": {
    "base_url": "http://localhost:8000/v1",
    "model": "Qwen/Qwen3.5-32B"
  }
}'
```

If you want both aliases available at once:

```bash
export OPENAI_COMPATIBLE_ENGINES='{
  "qwen3_chat": {
    "base_url": "http://localhost:8000/v1",
    "model": "Qwen/Qwen3-32B"
  },
  "qwen3.5_chat": {
    "base_url": "http://localhost:8000/v1",
    "model": "Qwen/Qwen3.5-32B"
  }
}'
```

Notes:

- No API key is required for a normal local unauthenticated vLLM server.
- If your local server insists on a bearer token, set any dummy token and add `api_key` or `api_key_env` to the alias config.
- If a Qwen variant performs better without a system prompt, add `"omit_system_prompt": true` inside that alias config.


## 3. Quick Connectivity Check

Optional sanity check:

```bash
curl http://localhost:8000/v1/models
```

You should see your served model listed.


## 4. Run `llm_planning_analysis`

This is the newer benchmark stack. It supports:

- plan generation
- zero-shot plan generation
- chain-of-thought / state-tracking
- PDDL prompting
- zero-shot PDDL prompting

Move into the directory:

```bash
cd /workspaces/LLMs-Planning/llm_planning_analysis
```

### Full pipeline

Qwen3:

```bash
python3 llm_plan_pipeline.py \
  --task t1_zero \
  --config blocksworld \
  --engine qwen3_chat \
  --translator_engine qwen3_chat \
  --max_workers 1
```

Qwen3.5:

```bash
python3 llm_plan_pipeline.py \
  --task t1_zero \
  --config blocksworld \
  --engine qwen3.5_chat \
  --translator_engine qwen3.5_chat \
  --max_workers 1
```

### All task ids in `llm_planning_analysis`

- `t1`: plan generation
- `t1_zero`: zero-shot plan generation
- `t1_cot`: state-tracking / CoT plan generation
- `t1_pddl`: PDDL plan generation
- `t1_zero_pddl`: zero-shot PDDL plan generation

Example:

```bash
python3 llm_plan_pipeline.py --task t1_pddl --config logistics --engine qwen3_chat --translator_engine qwen3_chat
```

### Run only prompt generation

```bash
python3 prompt_generation.py --task t1_zero --config blocksworld
```

### Run only response generation

```bash
python3 response_generation.py --task t1_zero --config blocksworld --engine qwen3_chat --max_workers 1
```

### Run only evaluation

Use the same translator alias if you want Qwen to do extraction during evaluation:

```bash
python3 response_evaluation.py --task t1_zero --config blocksworld --engine qwen3_chat --translator_engine qwen3_chat
```

If you want rule-based extraction only:

```bash
python3 response_evaluation.py --task t1_zero --config blocksworld --engine qwen3_chat --no_llm_based_extraction
```


## 5. Run Backprompting in `llm_planning_analysis`

This is the iterative critique / verifier loop.

Move into the directory:

```bash
cd /workspaces/LLMs-Planning/llm_planning_analysis
```

Typical command pattern:

```bash
python3 back_prompting_parallel.py \
  --config blocksworld \
  --engine qwen3_chat \
  --task t1_zero_pddl \
  --max_workers 1
```

If you want Qwen3.5 instead:

```bash
python3 back_prompting_parallel.py \
  --config blocksworld \
  --engine qwen3.5_chat \
  --task t1_zero_pddl \
  --max_workers 1
```

Important note:

- Backprompting has many flags and naming conventions.
- Run `python3 back_prompting_parallel.py --help` to see the exact combinations supported by this repo snapshot.
- The patched engine routing covers the generator/verifier chat calls in this path.


## 6. Run `plan-bench`

This is the older benchmark stack with the broader task suite.

Move into the directory:

```bash
cd /workspaces/LLMs-Planning/plan-bench
```

### Full pipeline

Qwen3:

```bash
python3 llm_plan_pipeline.py \
  --task t1 \
  --config blocksworld \
  --engine qwen3_chat
```

Qwen3.5:

```bash
python3 llm_plan_pipeline.py \
  --task t1 \
  --config blocksworld \
  --engine qwen3.5_chat
```

### All task ids in `plan-bench`

- `t1`: plan generation
- `t2`: optimal planning
- `t3`: plan verification
- `t4`: plan reuse
- `t5`: plan generalization
- `t6`: replanning
- `t7`: reasoning about plan execution
- `t8_1`: goal reformulation, goal shuffling
- `t8_2`: goal reformulation, full to partial
- `t8_3`: goal reformulation, partial to full

Example:

```bash
python3 llm_plan_pipeline.py --task t7 --config logistics --engine qwen3_chat
```

### Run only prompt generation

```bash
python3 prompt_generation.py --task t3 --config blocksworld
```

### Run only response generation

```bash
python3 response_generation.py --task t3 --config blocksworld --engine qwen3_chat
```

### Run only evaluation

```bash
python3 response_evaluation.py --task t3 --config blocksworld --engine qwen3_chat
```


## 7. Output Locations

`llm_planning_analysis` writes to:

- `llm_planning_analysis/prompts/...`
- `llm_planning_analysis/responses/<domain>/<engine>/...`
- `llm_planning_analysis/results/<domain>/<engine>/...`
- `llm_planning_analysis/results_backprompting/<domain>/<engine>/...`

`plan-bench` writes to:

- `plan-bench/prompts/...`
- `plan-bench/responses/<domain>/<engine>/...`
- `plan-bench/results/<domain>/<engine>/...`


## 8. Recommended First Runs

Start with one simple command in each stack before launching larger sweeps.

`llm_planning_analysis`:

```bash
cd /workspaces/LLMs-Planning/llm_planning_analysis
python3 llm_plan_pipeline.py --task t1_zero --config blocksworld --engine qwen3_chat --translator_engine qwen3_chat --specific_instances 1 2 3
```

`plan-bench`:

```bash
cd /workspaces/LLMs-Planning/plan-bench
python3 llm_plan_pipeline.py --task t1 --config blocksworld --engine qwen3_chat --specific_instances 1 2 3
```


## 9. Common Failure Modes

### The model alias is not recognized

Cause:

- `OPENAI_COMPATIBLE_ENGINES` is not exported in the current shell.

Fix:

- Re-export the variable in the same shell where you run the Python command.

### Connection refused

Cause:

- vLLM is not running, or the port is wrong.

Fix:

- Check `curl http://localhost:8000/v1/models`

### Wrong model loaded

Cause:

- The alias points to a model id that does not match the currently served model.

Fix:

- Update the `model` field in `OPENAI_COMPATIBLE_ENGINES` to match the model shown by `/v1/models`.

### Evaluation works but extraction fails

Cause:

- In `llm_planning_analysis`, the evaluator uses `--translator_engine` for LLM-based plan extraction.

Fix:

- Pass `--translator_engine qwen3_chat` or `--translator_engine qwen3.5_chat`.
- Or use `--no_llm_based_extraction` if that task supports it and you want deterministic extraction.

### Throughput is unstable

Cause:

- Old code, aggressive parallelism, or a large model on limited hardware.

Fix:

- Start with `--max_workers 1`.
- Increase gradually only after a small run succeeds.


## 10. Practical Recommendation

If you want to benchmark both models cleanly:

1. Serve one model in vLLM.
2. Point one alias at it.
3. Run a small smoke test on 3 instances.
4. Run the full benchmark.
5. Stop vLLM.
6. Serve the other model.
7. Reuse the same commands with the other alias.

That avoids ambiguity about which actual model is behind `localhost:8000`.
