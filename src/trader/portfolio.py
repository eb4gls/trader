from file_io import scale
from positions import Positions
from reward import reward
from utils.dictionary import Dictionary


class Portfolio:
    configuration: Dictionary
    memory = None

    initial_budget = 0.
    budget = 0.

    latest_price: float = 0.
    forecast: float = 0.
    konkorde = 0.

    failed_actions = ['f.buy', 'f.sell']

    # These are the variables that MUST be saved by the `dump()` method
    # in `environment`, in order to be able to resume the state.
    state_variables = ['initial_budget', 'budget', 'latest_price', 'forecast',
                       'cost', 'portfolio_value', 'profit', 'shares',
                       'konkorde']

    def __init__(self,
                 configuration,
                 initial_price,
                 forecast,
                 env_memory):

        self.params = configuration
        self.display = self.params.display
        self.log = self.params.log
        self.initial_budget = scale(self.params.initial_budget, 0.,
                                    self.params.fcast_file.max_support)
        self.positions = Positions(configuration, self.initial_budget)
        self.reset(initial_price, forecast, env_memory)

    def reset(self, initial_price, forecast, env_memory):
        """
        Initializes portfolio to the initial state.
        """
        self.budget = self.initial_budget
        self.latest_price = initial_price
        self.forecast = forecast
        self.memory = env_memory
        self.konkorde = 0.
        self.positions.reset()

        self.log.debug('Portfolio reset. Initial budget: {:.1f}'.format(
            self.initial_budget))

    def wait(self):
        """
        WAIT Operation
        """
        action_name = 'wait'
        rw = reward.decide(action_name, self.positions)
        msg = '  WAIT: ' + \
              'prc({:.2f})|bdg({:.2f})|val({:.2f})|prf({:.2f})|cost({:.2f})'
        self.log.debug(msg.format(
            self.latest_price, self.budget, self.positions.value(),
            self.positions.profit(), self.positions.cost()))

        return action_name, rw

    def buy(self, num_shares: float = 1.0) -> object:
        """
        BUY Operation
        :param num_shares: number of shares. Default to 1.
        :return: The action executed and the reward obtained by the operation.
        """
        action_name = 'buy'
        buy_price = num_shares * self.latest_price
        if buy_price > self.budget:
            action_name = 'f.buy'
            self.log.debug('  FAILED buy')
            rw = reward.failed()
        else:
            rw = reward.decide(action_name, self.positions)
            self.budget -= self.positions.buy(num_shares,
                                              self.latest_price,
                                              self.params.mode)

        # self.update_after_buy(action_name, num_shares, buy_price)
        return action_name, rw

    def sell(self, num_shares=1.0):
        """
        SELL Operation
        :param num_shares: number of shares. Default to 1.
        :return: The action executed and the reward obtained by the operation.
        """
        action_name = 'sell'
        if num_shares > self.positions.num_shares():
            action_name = 'f.sell'
            self.log.debug('  FAILED sell')
            rw = reward.failed()
        else:
            rw = reward.decide(action_name, self.positions)
            income, profit = self.positions.sell(num_shares, self.latest_price)
            self.budget += (income + profit)
            self.log.debug('  Sell op -> income:{:.2f}, profit:{:.2f}'.format(
                income, profit))
            self.log.debug('  Budget -> {:.2f} + {:.2f}'.format(
                self.budget, (income + profit)))

        return action_name, rw

    def update(self, price, forecast, konkorde=None):
        """
        Updates portfolio after an iteration step.

        :param price:    new price registered
        :param forecast: new forecast registered
        :param konkorde: the konkorde value (computed from green & blue read
                         the data file, if applicable)
        :return:         the portfolio object
        """
        self.latest_price = price
        self.forecast = forecast
        if konkorde is not None:
            self.konkorde = konkorde
        self.positions.update(self.latest_price)

        # self.portfolio_value = self.num_shares * self.latest_price
        self.log.debug('  Updating portfolio after STEP.')
        msg = '  > portfolio_value={:.2f}, latest_price={:.2f}, forecast={:.2f}'
        self.log.debug(msg.format(
            self.positions.value(), self.latest_price, self.forecast))
        self.positions.debug()
        return self

    def values_to_record(self):
        cost = self.positions.cost()
        profit = self.positions.profit()
        values = [
            self.latest_price,
            self.forecast,
            self.budget,
            cost,
            self.positions.value(),
            profit,
            self.budget + cost + profit,
            self.positions.num_shares()
        ]
        if self.params.have_konkorde:
            values += [self.konkorde]
        values += ['', 0., 0., '']
        return values

    def failed_action(self, action, price):
        """
        Determines if the action can be done or will be a failed operation
        """
        if action == self.params.action.index('buy'):
            if price > self.budget:
                return True
            else:
                return False
        elif action == self.params.action.index('sell'):
            if self.positions.num_shares() == 0.:
                return True
            else:
                return False
        else:
            return False

    @property
    def gain(self):
        return self.positions.profit() > 0

    @property
    def last_gain(self):
        return self.memory.last('profit') > 0.

    @property
    def prev_last_gain(self):
        return self.memory.prevlast('profit') > 0.

    @property
    def have_shares(self):
        return self.positions.num_shares() > 0

    @property
    def can_buy(self) -> bool:
        return self.budget >= self.latest_price

    @property
    def can_sell(self) -> bool:
        return self.positions.num_shares() > 0.

    @property
    def prediction_upward(self):
        msg = '  Pred sign ({}) latest price({:.2f}) vs. last_forecast({:.2f})'
        self.log.debug(
            msg.format(
                '↑' if self.latest_price <= self.forecast else '↓',
                self.latest_price, self.forecast))
        return self.latest_price <= self.forecast

    @property
    def last_forecast(self):
        self.log.debug('    Last forecast in MEM = {:.2f}'.format(
            self.memory.last('forecast')))
        return self.memory.last('forecast')

    @property
    def last_price(self):
        # self.log.debug(
        #    '    Last price in MEM = {:.2f}'.format(self.memory.last('price')))
        return self.memory.last('price')

    @property
    def prevlast_forecast(self):
        # self.log.debug(
        #     '    PrevLast forecast in MEM = {:.2f}'.format(
        #         self.memory.prevlast('forecast')))
        return self.memory.prevlast('forecast')

    @property
    def prevlast_price(self):
        # self.log.debug(
        #     '    PrevLast price in MEM = {:.2f}'.format(
        #         self.memory.prevlast('price')))
        return self.memory.prevlast('price')

    @property
    def prevprevlast_forecast(self):
        # self.log.debug(
        #     '    PrevPrevLast forecast in MEM = {:.2f}'.format(
        #         self.memory.prevprevlast('forecast')))
        return self.memory.prevprevlast('forecast')

    @property
    def prevprevlast_price(self):
        # self.log.debug(
        #     '    PrevPrevLast price in MEM = {:.2f}'.format(
        #         self.memory.prevprevlast('price')))
        return self.memory.prevprevlast('price')
