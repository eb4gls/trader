import argparse


class Arguments(object):
    args = None
    possible_actions = ['konkorde']
    parser: argparse.ArgumentParser = None

    def __init__(self, *args):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument(
            'action', nargs='?', default='konkorde',
            help='what indicator to compute',
            choices=self.possible_actions)
        self.parser.add_argument(
            '-c', '--config-file', nargs=1, type=str,
            help='Relative path to configuration file to be used (YAML).')
        self.parser.add_argument(
            '-f', '--file', nargs=1, type=str,
            required=True,
            help='Input OHLCV File to process')
        self.parser.add_argument(
            '-t', '--today', action='store_true',
            help='Computes only today\'s value')
        self.parser.add_argument(
            '--scaler-file', nargs=1, type=str,
            help='What scaler to use for single index computation')
        self.parser.add_argument(
            '-m', '--merge-to-file', nargs=1, type=str,
            help='Merge index into specified file')
        self.parser.add_argument(
            '-o', '--output', nargs=1, type=str,
            help='Output filename to be used to save results')
        self.parser.add_argument(
            '-s', '--save', action='store_true',
            help='Append index to the input file')
        self.parser.add_argument(
            '-d', '--debug', nargs=1, type=int,
            help='Debug level (0..4), default 0.')

        self.args = self.parser.parse_args()
        action_name = 'arg_{}'.format(self.args.action)
        setattr(self, action_name, True)
        for action in set(self.possible_actions) - {action_name[1:]}:
            setattr(self, 'arg_{}'.format(action), False)
