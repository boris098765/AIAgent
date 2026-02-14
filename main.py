from core.app.bootstrap import DEFAULT_SYSTEM_PROMPT, build_agent


if __name__ == "__main__":
    agent = build_agent(DEFAULT_SYSTEM_PROMPT)

    while True:
        user_input = input(">>> ")
        result = agent.run(user_input)
        print(result)
