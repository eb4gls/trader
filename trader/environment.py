import importlib

import pandas as pd

from portfolio import Portfolio
from scombiner import SCombiner


class Environment(object):
    max_states_ = 0
    data_ = None
    current_state_ = 0
    t = 0
    portfolio_ = None
    price_ = 0.
    forecast_ = 0.
    max_actions_ = 0
    done_ = False
    reward_ = 0.
    new_state_: int = 0
    debug = False

    def __init__(self, context_dictionary, debug=False):
        # First, update the internal dictionary with the parameters read.
        self.__dict__.update(context_dictionary)
        self.context_dictionary = context_dictionary

        self.debug = debug
        self.read_data(self._data_path)
        self.set_price()
        self.portfolio_ = Portfolio(self.__dict__,
                                    self.price_,
                                    self.forecast_,
                                    debug)
        self.states = SCombiner(self._states_list)
        self._num_states = self.states.max_id
        self.update_state()

        # Update the original contextual dictionary with the
        # new parameters just set in this constructor
        context_dictionary.update(self.__dict__)

    def log(self, *args, **kwargs):
        if self.debug is True:
            print(*args, **kwargs)

    def reset(self, debug=False):
        """
        Reset all internal states
        :param debug:
        :return:
        """
        self.debug = debug
        del self.portfolio_
        self.done_ = False
        self.t = 0
        self.set_price()
        self.portfolio_ = Portfolio(self.__dict__,
                                    self.price_,
                                    self.forecast_,
                                    self.debug)
        return self.update_state()

    def read_data(self, path):
        """
        Reads the simulation data.
        :param path:
        :return:
        """
        self.data_ = pd.read_csv(path)
        self.max_states_ = self.data_.shape[0]

    def set_price(self):
        """
        Set the price to the current time slot,
        reading column 0 from DF
        """
        assert self.data_ is not None, 'Price series data has not been read yet'
        self.price_ = self.data_.iloc[self.t, 0]
        self.forecast_ = self.data_.iloc[self.t, 1]

    @staticmethod
    def decide_next_action(state, strategy):
        return strategy[state]

    def update_state(self):
        """
        Determine the state of my portfolio value
        :return: New state
        """
        # Iterate through the list of states defined in the parameters file
        # and call the update_state() static method in them.
        new_substates = []
        for module_param_name in self._state.keys():
            # The extended classes are defined in the params file and must
            # start with the 'state_' string.
            # The '[1:]' serves to remove the leading underscore.
            module_name = 'state_' + module_param_name[1:]
            module = importlib.import_module(module_name)
            new_substates.append(
                getattr(module, module_name).update_state(self.portfolio_))

        # Get the ID resulting from the combination of the sub-states
        self.current_state_ = self.states.get_id(*new_substates)
        return self.current_state_

    def step(self, action):
        """
        Send an action to my Environment.
        :param action: the action.
        :return: state, reward, done and iter count.
        """
        assert action < self._num_actions, \
            'Action ID must be between 0 and {}'.format(
                self._num_actions)

        if action == self._action_name.do_nothing:
            self.portfolio_.do_nothing()
            self.reward_ = 0.
        if action == self._action_name.buy:
            self.reward_ = self.portfolio_.buy()
        if action == self._action_name.sell:
            self.reward_ = self.portfolio_.sell()
        self.log(' | R: {:>+5.1f} | {:s}'.format(
            self.reward_, self.states.name(self.current_state_)))

        self.t += 1
        if self.t >= self.max_states_:
            self.done_ = True
            self.portfolio_.report(self.t - 1, disp_footer=True)
            self.log("")
            return self.new_state_, self.reward_, self.done_, self.t

        self.set_price()
        self.portfolio_.update(self.price_, self.forecast_)
        self.new_state_ = self.update_state()
        self.portfolio_.report(self.t)

        return self.new_state_, self.reward_, self.done_, self.t
