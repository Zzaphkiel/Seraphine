import asyncio
from abc import abstractmethod, ABC

from app.lol.tools import autoBan, autoPick, autoTrade, autoSwap


class Selection:
    def __init__(self):
        self._phase = Planning()

    def _change_phase(self, phase):
        if isinstance(phase, Phase):
            self._phase = phase

    async def act(self, data: dict):
        print(data)
        localPlayerCellId = data['localPlayerCellId']
        actions = data['actions']
        actionsInProgress = None
        for action_group in actions:
            for action in action_group:
                if action['isInProgress']:
                    actionsInProgress = action_group
                    break

        if asyncio.iscoroutinefunction(self._phase.conduct):
            self._change_phase(
                await self._phase.conduct(
                    data,
                    local_player_cell_id=localPlayerCellId,
                    actions_in_progress=actionsInProgress)
            )
        else:
            self._change_phase(
                self._phase.conduct(
                    data,
                    local_player_cell_id=localPlayerCellId,
                    actions_in_progress=actionsInProgress)
            )


class Phase(ABC):
    @abstractmethod
    def conduct(self, data: dict, *args, **kwargs):
        pass


class Planning(Phase):
    async def conduct(self, data: dict, *args, **kwargs):
        if data.get('pickOrderSwaps'):
            await autoSwap(data)
            return

        actions = kwargs.get('actions_in_progress')
        if actions:
            for action in actions:
                if (action['actorCellId'] == kwargs['local_player_cell_id']
                        and action['type'] == 'ban'):
                    await autoBan(data)
                    return Picking()


class Banning(Phase):
    async def conduct(self, data: dict, *args, **kwargs):
        actions = kwargs.get('actions_in_progress')
        if actions:
            for action in actions:
                if (action['actorCellId'] == kwargs['local_player_cell_id']
                        and action['type'] == 'ban'):
                    await autoBan(data)
                    return Picking()


class Picking(Phase):
    async def conduct(self, data: dict, *args, **kwargs):
        if data.get('pickOrderSwaps'):
            await autoSwap(data)
            return

        if kwargs.get('action'):
            if kwargs['action']['type'] == 'ban':
                await autoBan(data)
                return Picking()
            elif kwargs['action']['type'] == 'pick':
                await autoPick(data)
                return Waiting()


class Waiting(Phase):
    async def conduct(self, data: dict, *args, **kwargs):
        if data.get('trades'):
            await autoTrade(data)
            return


class GameStart(Phase):
    def conduct(self, data: dict, *args, **kwargs):
        pass
