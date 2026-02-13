from core.agent.agent import Agent


class SubAgent(Agent):
    def __init__(self, registry, objective: str):
        super().__init__(registry)
        self.objective = objective

    def run_objective(self):
        return self.run(self.objective)
