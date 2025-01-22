class CommunicationManager:
    def __init__(self, communication_strategy):
        self._strategy = communication_strategy

    def subscriber(self, **kwargs):
        return self._strategy.subscriber(**kwargs)

    def publisher(self, **kwargs):
        return self._strategy.publisher(**kwargs)

    def unsubscribe(self, **kwargs):
        return self._strategy.unsubscribe(**kwargs)