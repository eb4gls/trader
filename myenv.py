import pandas as pd
from portfolio import Portfolio

# Default initial budget
DEF_INITIAL_BUDGET = 10000.

# My Actions
DO_NOTHING = 0
BUY = 1
SELL = 2

# My States
EVEN_EVEN = 0
EVEN_WIN = 1
EVEN_LOSE = 2
WINNING_EVEN = 3
WINNING_WIN = 4
WINNING_LOSE = 5
LOOSING_EVEN = 6
LOOSING_WIN = 7
LOOSING_LOSE = 8

forecast_dict = {'even': 0, 'win': 1, 'lose': 2}
value_dict = {'even': 0, 'win': 3, 'lose': 6}

state_dict = {
    EVEN_EVEN: 'EVEN_EVEN',
    EVEN_WIN: 'EVEN_RISE',
    EVEN_LOSE: 'EVEN_FALL',
    WINNING_EVEN: 'WINNING_EVEN',
    WINNING_WIN: 'WINNING_RISE',
    WINNING_LOSE: 'WINNING_FALL',
    LOOSING_EVEN: 'LOOSING_EVEN',
    LOOSING_WIN: 'LOOSING_RISE',
    LOOSING_LOSE: 'LOOSING_FALL'
}
action_dict = {
    0: 'do_nothing',
    1: 'buy',
    2: 'sell'
}


class MyEnv:
    num_states_ = 0
    max_states_ = 0
    num_actions_ = 0
    data_ = None
    state_ = 0
    t = 0
    portfolio_ = None
    price_ = 0.
    forecast_ = 0.
    max_actions_ = 0
    done_ = False
    reward_ = 0.
    new_state_ = 0
    debug = False

    def __init__(self,
                 num_states=9,
                 num_actions=3,
                 path='forecast_Gold_Inflation',
                 debug=False):
        self.debug = debug
        self.num_actions_ = num_actions
        self.num_states_ = num_states
        self.read_data(path)
        self.set_price()
        self.portfolio_ = Portfolio(DEF_INITIAL_BUDGET,
                                    self.price_,
                                    self.forecast_,
                                    debug)
        self.set_state()
        return

    def log(self, *args, **kwargs):
        if self.debug is True:
            print(*args, **kwargs)

    def reset(self, debug=False):
        self.debug=debug
        del self.portfolio_
        self.done_ = False
        self.t = 0
        self.set_price()
        self.portfolio_ = Portfolio(DEF_INITIAL_BUDGET,
                                    self.price_,
                                    self.forecast_,
                                    self.debug)
        self.set_state()
        return self.state_

    def set_state(self):
        # state of my budget
        if self.portfolio_.budget == self.portfolio_.initial_budget:
            value = 'even'
        elif self.portfolio_.budget > self.portfolio_.initial_budget:
            value = 'win'
        else:
            value = 'lose'
        # guess what the state, given the forecast
        if self.portfolio_.forecast == self.portfolio_.latest_price:
            forecast = 'even'
        elif self.portfolio_.forecast > self.portfolio_.latest_price:
            forecast = 'win'
        else:
            forecast = 'lose'
        self.state_ = value_dict[value] + forecast_dict[forecast]
        return self.state_

    def read_data(self, path):
        self.data_ = pd.read_csv(path)
        self.max_states_ = self.data_.shape[0]

    def set_price(self):
        """ Set the price to the current time slot, reading column 0 from DF """
        assert self.data_ is not None, 'Price series data hasn\'t been read yet'
        self.price_ = self.data_.iloc[self.t, 0]
        self.forecast_ = self.data_.iloc[self.t, 1]

    def step(self, action):
        assert action < self.num_actions_, \
            'Action ID must be between 0 and {}'.format(
                self.num_actions_)

        if action == DO_NOTHING:
            self.portfolio_.do_nothing()
            self.reward_ = 0.
        if action == BUY:
            self.reward_ = self.portfolio_.buy()
        if action == SELL:
            self.reward_ = self.portfolio_.sell()
        self.log(' | R: {:>+5.1f} | {:s}'.format(
            self.reward_, state_dict[self.state_]))

        self.t += 1
        if self.t >= self.max_states_:
            self.done_ = True
            self.portfolio_.report(self.t - 1, disp_footer=True)
            self.log("")
            return self.new_state_, self.reward_, self.done_, self.t

        self.set_price()
        self.portfolio_.update(self.price_, self.forecast_)
        self.new_state_ = self.set_state()
        self.portfolio_.report(self.t)

        return self.new_state_, self.reward_, self.done_, self.t

    def decide(self, state, strategy):
        return strategy[state]