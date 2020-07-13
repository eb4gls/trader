from unittest import TestCase

import pandas as pd

from cs_encoder import CSEncoder
from my_dict import MyDict


def do_nothing(*args, **kwargs):
    pass


class TestCSEncoder(TestCase):

    params = MyDict()
    params.log = MyDict()
    params.log.debug = do_nothing
    params.log.info = do_nothing
    params.input_file = 'DAX100.csv'
    params.subtypes = ['body', 'move']

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(TestCSEncoder, cls).setUpClass()
        # Defining a type A, G, M, Q, W and Z
        data = pd.DataFrame({
            'o': [50., 80., 10., 80., 10., 100],
            'h': [100, 100, 100, 100, 100, 100],
            'l': [00., 00., 00., 00., 00., 00.],
            'c': [51., 70., 30., 40., 70., 00.],
            'v': [100, 830, 230, 660, 500, 120]
        })
        date_column = pd.DataFrame({
            'Date': pd.date_range('2020-06-01', '2020-06-06', freq='D')
        })
        data = pd.concat([date_column, data], axis=1)
        data = data.set_index('Date')
        # mpf.plot(data, columns=['o','h','l','c','v'], type='candle',
        # style='charles')
        cls.data = data

    def test_CSEncoder(self):
        """
        Test the constructor. Normally called without any tick in the
        arguments, it
        """
        cse = CSEncoder(self.params)
        self.assertEqual(cse.open, 0.)
        self.assertEqual(cse.close, 0.)
        self.assertEqual(cse.high, 0.)
        self.assertEqual(cse.low, 0.)
        self.assertEqual(cse.min, 0.)
        self.assertEqual(cse.max, 0.)

        # Initialization
        self.assertEqual(cse.encoded_delta_close, 'pA')
        self.assertEqual(cse.encoded_delta_high, 'pA')
        self.assertEqual(cse.encoded_delta_low, 'pA')
        self.assertEqual(cse.encoded_delta_max, 'pA')
        self.assertEqual(cse.encoded_delta_min, 'pA')
        self.assertEqual(cse.encoded_delta_open, 'pA')

    def test_correct_encoding(self):
        """
        Test if this method is correctly capturing that column names reflect
        what the encoding is saying.
        """
        self.assertTrue(
            CSEncoder(self.params, encoding='ohlc').correct_encoding())
        self.assertTrue(
            CSEncoder(self.params, encoding='OHLC').correct_encoding())
        self.assertFalse(
            CSEncoder(self.params, encoding='0hlc').correct_encoding())
        self.assertFalse(
            CSEncoder(self.params, encoding='ohl').correct_encoding())
        self.assertFalse(
            CSEncoder(self.params, encoding='').correct_encoding())

    def test_fit(self):
        """
        Measure main indicators for encoding of the second tick in the
        test data. I use the second one to be able to compare it against
        the first one.
        """
        encoder = CSEncoder(self.params, values=self.data.iloc[1])
        encoder = encoder.fit(self.data)
        self.assertEqual(encoder.cse_zero_open, 50.)
        self.assertEqual(encoder.cse_zero_high, 100.)
        self.assertEqual(encoder.cse_zero_low, 0.)
        self.assertEqual(encoder.cse_zero_close, 51.)
        self.assertTrue(encoder.fitted)
        for subtype in self.params.subtypes:
            self.assertIsNotNone(encoder.onehot[subtype])

    def test_calc_parameters(self):
        """
        Test if the parameters computed for a sample tick are correct.
        """
        cse = CSEncoder(self.params, self.data.iloc[1])

        self.assertIsNot(cse.positive, cse.negative)
        self.assertFalse(cse.positive)
        self.assertTrue(cse.negative)

        # Percentiles, etc...
        self.assertLessEqual(cse.body_relative_size, 0.1, 'Body relative size')
        self.assertEqual(cse.hl_interval_width, 100.)
        self.assertEqual(cse.oc_interval_width, 10.)
        self.assertEqual(cse.mid_body_point, 75.)
        self.assertEqual(cse.mid_body_percentile, 0.75)
        self.assertEqual(cse.min_percentile, 0.7)
        self.assertEqual(cse.max_percentile, 0.8)
        self.assertEqual(cse.upper_shadow_len, 20.)
        self.assertEqual(cse.upper_shadow_percentile, 0.2)
        self.assertEqual(cse.lower_shadow_len, 70.)
        self.assertEqual(cse.lower_shadow_percentile, 0.7)
        self.assertEqual(cse.body_relative_size, 0.1)
        self.assertAlmostEqual(cse.shadows_relative_diff, 0.5)

        # Body position.
        self.assertFalse(cse.body_in_center)
        self.assertFalse(cse.body_in_lower_half)
        self.assertTrue(cse.body_in_upper_half)
        self.assertTrue(cse.has_both_shadows)
        self.assertTrue(cse.has_lower_shadow)
        self.assertTrue(cse.has_upper_shadow)
        self.assertFalse(cse.shadows_symmetric)

    def test_ticks2cse(self):
        """
        Test the method in charge of transforming an entire list of
        ticks into CSE format. It's only goal is to retun an array with
        all of them.
        """
        encoder = CSEncoder(self.params).fit(self.data)
        cse = encoder.ticks2cse(self.data)
        self.assertEqual(len(cse), 6)
        for i in range(len(cse)):
            self.assertIsInstance(cse[i], CSEncoder)
