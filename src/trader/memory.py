from pandas import DataFrame, Series


# TODO Hacer esta clase generica para poder manejar varios dataframes

class Memory:

    def __init__(self, configuration):
        self.params = configuration
        self.log = self.params.log
        # Create a DataFrame within the configuration to store all the values
        # that are relevant to later perform data analysis.
        # The YAML file contains the column names in a parameter called
        # table_headers.
        self.results = DataFrame(columns=self.params.table_headers)

    def record_state(self, portfolio, t: int, ts: str):
        """
        Records the values from portfolio in a new memory position
        :param portfolio:
        :param t: instant in time during simulation
        :param ts: the timestamp of the entry
        :return: None
        """
        values = [t] + [ts] + portfolio.values_to_record()
        row = Series(dict(zip(self.params.table_headers, values)))
        self.results = self.results.append(row, ignore_index=True)
        self.log.debug('  Recorded values (ts={})'.format(ts))

    def record_action_and_reward(
            self,
            action_name,
            reward,
            current_state,
            description):
        """
        Record action selected in results table.
        :param action_name:
        :param reward:
        :param current_state:
        :param description:
        :return: None
        """
        last_index = self.results.shape[0] - 1
        self.results.loc[last_index, 'action'] = action_name
        self.results.loc[last_index, 'reward'] = reward
        self.results.loc[last_index, 'state'] = current_state
        self.results.loc[last_index, 'state_desc'] = description
        self.log.debug(
            '  Reward ({:.2f}), recorded to action \'{}\' in state {}'.format(
                reward, action_name, current_state))

    def reset(self):
        if self.results.shape[0] > 0:
            self.results = self.results[0:0]

    def last(self, column_name):
        if self.len >= 1:
            return self.results.iloc[-1][column_name]
        else:
            return 0.

    def prevlast(self, column_name):
        if self.len >= 2:
            return self.results.iloc[-2][column_name]
        else:
            return 0.

    def prevprevlast(self, column_name):
        if self.len >= 3:
            return self.results.iloc[-3][column_name]
        else:
            return 0.

    @property
    def len(self):
        return self.results.shape[0]
