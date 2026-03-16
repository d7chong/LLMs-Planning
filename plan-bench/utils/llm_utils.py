from transformers import StoppingCriteriaList, StoppingCriteria
from openai import OpenAI
import os
import json

client = OpenAI()


def _load_openai_compatible_engines():
    raw_config = os.getenv("OPENAI_COMPATIBLE_ENGINES", "").strip()
    if not raw_config:
        return {}
    try:
        config = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        raise ValueError("OPENAI_COMPATIBLE_ENGINES must be valid JSON") from exc
    if not isinstance(config, dict):
        raise ValueError("OPENAI_COMPATIBLE_ENGINES must decode to a JSON object")
    return config


def _resolve_engine_config(engine):
    compat_engines = _load_openai_compatible_engines()
    if engine in compat_engines:
        cfg = compat_engines[engine]
        if not isinstance(cfg, dict):
            raise ValueError(f"Engine config for {engine} must be a JSON object")
        return cfg
    return None


def _resolve_api_key(engine, engine_cfg):
    api_key = engine_cfg.get("api_key")
    if api_key:
        return api_key
    api_key_env = engine_cfg.get("api_key_env")
    if api_key_env:
        return os.environ[api_key_env]
    if engine.endswith("_chat"):
        return os.environ.get("OPENAI_API_KEY")
    return None


def _get_chat_client_and_model(engine):
    engine_cfg = _resolve_engine_config(engine)
    if engine_cfg is None:
        return client, engine.split("_")[0], {}

    base_url = engine_cfg.get("base_url")
    model_name = engine_cfg.get("model")
    if not base_url or not model_name:
        raise ValueError(f"Engine config for {engine} must define base_url and model")

    api_key = _resolve_api_key(engine, engine_cfg)
    compat_client = OpenAI(api_key=api_key, base_url=base_url)
    return compat_client, model_name, engine_cfg


def _default_messages(query, engine, engine_cfg=None):
    engine_cfg = engine_cfg or {}
    if engine_cfg.get("omit_system_prompt", False):
        return [{"role": "user", "content": query}]

    system_prompt = engine_cfg.get(
        "system_prompt",
        "You are the planner assistant who comes up with correct plans.",
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query},
    ]


def generate_from_bloom(model, tokenizer, query, max_tokens):
    encoded_input = tokenizer(query, return_tensors='pt')
    stop = tokenizer("[PLAN END]", return_tensors='pt')
    stoplist = StoppingCriteriaList([stop])
    output_sequences = model.generate(input_ids=encoded_input['input_ids'].cuda(), max_new_tokens=max_tokens,
                                      temperature=0, top_p=1)
    return tokenizer.decode(output_sequences[0], skip_special_tokes=True)


def send_query(query, engine, max_tokens, model=None, stop="[STATEMENT]"):
    max_token_err_flag = False
    if engine == 'bloom':

        if model:
            response = generate_from_bloom(model['model'], model['tokenizer'], query, max_tokens)
            response = response.replace(query, '')
            resp_string = ""
            for line in response.split('\n'):
                if '[PLAN END]' in line:
                    break
                else:
                    resp_string += f'{line}\n'
            return resp_string
        else:
            assert model is not None
    elif engine == 'finetuned':
        if model:
            try:
                response = client.completions.create(
                    model=model['model'],
                    prompt=query,
                    temperature=0,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                    stop=["[PLAN END]"])
            except Exception as e:
                max_token_err_flag = True
                print("[-]: Failed GPT3 query execution: {}".format(e))
            text_response = response["choices"][0]["text"] if not max_token_err_flag else ""
            return text_response.strip()
        else:
            assert model is not None
    elif '_chat' in engine:
        compat_client, eng, engine_cfg = _get_chat_client_and_model(engine)
        messages = _default_messages(query, engine, engine_cfg)
        try:
            request_args = {
                "model": eng,
                "messages": messages,
            }
            if len(messages) > 1:
                request_args["temperature"] = 0
            response = compat_client.chat.completions.create(**request_args)
        except Exception as e:
            max_token_err_flag = True
            print("[-]: Failed GPT3 query execution: {}".format(e))
        text_response = response.choices[0].message.content if not max_token_err_flag else ""
        return text_response.strip()        
    else:
        try:
            response = client.completions.create(
                model=engine,
                prompt=query,
                temperature=0,
                max_tokens=max_tokens,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=stop)
        except Exception as e:
            max_token_err_flag = True
            print("[-]: Failed GPT3 query execution: {}".format(e))

        text_response = response.choices[0].text if not max_token_err_flag else ""
        return text_response.strip()
