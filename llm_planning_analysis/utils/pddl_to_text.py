

import random


def _normalize_plan_lines(plan_lines):
    lines = [line.rstrip() for line in plan_lines if line.strip()]
    if lines and lines[-1].startswith(";"):
        lines = lines[:-1]
    return lines


def _get_plan_lines(plan_text=None, plan_file="sas_plan"):
    if plan_text is not None:
        return _normalize_plan_lines(plan_text.splitlines())
    try:
        with open(plan_file) as f:
            return _normalize_plan_lines(f.readlines())
    except FileNotFoundError:
        return []

def get_sorted(init_atoms):
    return sorted(init_atoms, key=lambda x: x.symbol.name + " " + " ".join([subterm.name for subterm in x.subterms]))

def parse_problem(problem, data, shuffle):
    def parse(init_goal_preds, OBJS):
        TEXT = ""
        predicates = []

        init_goal_preds = list(init_goal_preds)
        for atom in init_goal_preds:
            objs = []
            for subterm in atom.subterms:
                if 'obfuscated' in data["domain_name"]:
                    objs.append(subterm.name.replace('o','object_'))
                elif 'blocksworld' in data['domain_name']:
                    objs.append(OBJS[subterm.name])
                elif 'logistics' in data['domain_name']:
                    obj = subterm.name
                    objs.append(f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}")
                # ADD SPECIFIC TRANSLATION FOR EACH DOMAIN HERE
            try:
                pred_string = data['predicates'][atom.symbol.name].format(*objs)
                predicates.append(pred_string)
            except:
                # print("[-]: Predicate not found in predicates dict: {}".format(atom.symbol.name))
                pass
            
        if len(predicates) > 1:
            TEXT += ", ".join(predicates[:-1]) + f" and {predicates[-1]}"
        else:
            TEXT += predicates[0]
        return TEXT

    OBJS = data['encoded_objects']

    init_atoms = get_sorted(problem.init.as_atoms())
    goal_preds = get_sorted(problem.goal.subformulas) if hasattr(problem.goal, 'subformulas') else [problem.goal]

    if shuffle:
        random.shuffle(init_atoms)
        random.shuffle(goal_preds)
    # print(shuffle,init_atoms)
    # print(goal_preds)
    # ----------- INIT STATE TO TEXT ----------- #
    INIT = parse(init_atoms, OBJS)

    # ----------- GOAL TO TEXT ----------- #
    GOAL = parse(goal_preds, OBJS)

    return INIT, GOAL
def fill_template(INIT, GOAL, PLAN, data, zero_shot=False, o4=False, instruction=None):
    if instruction is not None:
        zero_shot = instruction
    text = ""
    if INIT != "":
        text += "\n[STATEMENT]\n"
        text += f"As initial conditions I have that: {INIT.strip()}."
    if GOAL != "":
        text += f"\nMy goal is for the following to be true: {GOAL}."
    if not zero_shot:
        if o4:
            text += f"\n\nProvide the plan for the above problem between these two tags [PLAN] and [PLAN END]."
        else:
            text += f"\n\nMy plan is as follows:\n\n[PLAN]{PLAN}"
    else:
        text += f"\n\nTo solve the problem, you will have to provide which actions to take from the initial conditions and in which order in order to achieve the goal conditions. Provide the plan by giving the action names along with the objects \"ACTION_NAME OBJECTS\". Provide the plan between these two tags [PLAN] and [PLAN END]."

    # TODO: Add this replacement to the yml file -- Use "Translations" dict in yml
    if 'blocksworld' in data['domain_name']:
        text = text.replace("-", " ").replace("ontable", "on the table")
    return text

def instance_to_text(problem, get_plan, data, shuffle=False, plan=None):
    """
    Function to make an instance into human-readable format
    """

    OBJS = data['encoded_objects']

    # ----------- PARSE THE PROBLEM ----------- #
    INIT, GOAL = parse_problem(problem, data, shuffle)

    # ----------- PLAN TO TEXT ----------- #
    PLAN = ""
    if get_plan:
        PLAN = "\n"
        if plan is None:
            plan = _get_plan_lines()
        elif isinstance(plan, str):
            plan = _get_plan_lines(plan_text=plan)

        for action in plan:
            action = action.strip("(").strip(")")
            act_name, objs = action.split(" ")[0], action.split(" ")[1:]
            if 'obfuscated' in data["domain_name"]:
                objs = [j.replace('o','object_') for j in objs]
            elif 'blocksworld' in data['domain_name']:
                objs = [OBJS[obj] for obj in objs]
            elif 'logistics' in data['domain_name']:
                objs = [f"{OBJS[obj[0]].format(*[chr for chr in obj if chr.isdigit()])}" for obj in objs] 
            # ADD SPECIFIC TRANSLATION FOR EACH DOMAIN HERE
        
            PLAN += data['actions'][act_name].format(*objs) + "\n"
        PLAN += "[PLAN END]\n"

    return INIT, GOAL, PLAN, data









def get_plan_as_text(data, given_plan=None, plan_text=None):
    OBJS = data['encoded_objects']
    PLAN = ""
    # print(given_plan)
    if given_plan:
        for action in given_plan:
            act_name, objs = action.split("_")[0], action.split("_")[1:]
            PLAN += "(" + act_name + " " + " ".join(objs) + ")\n"
            # PLAN += data['actions'][act_name].format(*objs) + "\n"
        return PLAN

    plan = _get_plan_lines(plan_text=plan_text)

    for action in plan:
        action = action.strip("(").strip(")")
        act_name, objs = action.split(" ")[0], action.split(" ")[1:]
        PLAN += "(" + act_name + " " + " ".join(objs) + ")\n"
        # PLAN += data['actions'][act_name].format(*objs) + "\n"
    return PLAN
