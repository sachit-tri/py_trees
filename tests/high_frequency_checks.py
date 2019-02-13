import asyncio
import time

import py_trees


class HighFrequencyDecorator(py_trees.decorators.Decorator):
    def __init__(self, child, name: str = py_trees.common.Name.AUTO_GENERATED):
        super().__init__(child=child, name=name)
        self.cached_status = None
        self.status_changed = False

    def tick(self):
        if self.cached_status:
            # ignore the child
            for node in py_trees.behaviour.Behaviour.tick(self):
                yield node
        else:
            yield from super().tick()

    def update(self):
        if self.status_changed:
            cache = self.cached_status
            self.cached_status = None
            self.status_changed = False
            return cache
        else:
            current_status = self.decorated.status
            if self.cached_status != current_status:
                self.cached_status = current_status
                self.status_changed = True
            return current_status


class HighFrequencyActiveVisitor(py_trees.visitors.VisitorBase):
    def __init__(self):
        super().__init__(full=False)
        self.current_states = {}

    def initialise(self):
        self.current_states = {}

    def run(self, behaviour):
        if (behaviour.status != py_trees.common.Status.INVALID) and isinstance(behaviour, HighFrequencyDecorator):
            self.current_states[behaviour] = behaviour.status


class Tester:
    def __init__(self):
        self.visitor = HighFrequencyActiveVisitor()

    async def high_frequency_check(self):
        last_states = self.visitor.current_states
        new_states = last_states

        if len(last_states) > 0:
            while new_states == last_states:
                new_states = {}
                for node in self.visitor.current_states.keys():
                    node.tick_once()
                    new_states[node] = node.status

    async def tick(self, root):
        tree = py_trees.trees.BehaviourTree(root=root)
        tree.visitors.append(self.visitor)

        tree.tick()
        while tree.root.status not in [py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE]:
            await self.high_frequency_check()
            tree.tick()
            await asyncio.sleep(0.1)

            py_trees.display.print_ascii_tree(tree.root, show_status=True)

        print("Tree Ticks {}".format(tree.count))


def main():
    count = py_trees.behaviours.Count(fail_until=-1,
                                      running_until=5,
                                      success_until=float("inf"),
                                      reset=False)
    high = HighFrequencyDecorator(child=count)

    other_counter = py_trees.behaviours.Count(fail_until=-1, running_until=11, success_until=float("inf"), reset=False)
    other_counter_1 = HighFrequencyDecorator(py_trees.behaviours.Count(fail_until=-1, running_until=11, success_until=float("inf"), reset=False))
    seq = py_trees.composites.Sequence(children=[other_counter, other_counter_1, high])
    tester = Tester()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(tester.tick(seq)))
    loop.close()


if __name__ == "__main__":
    main()
