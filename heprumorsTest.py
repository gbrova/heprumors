import unittest
import heprumors

class TestTwitter(unittest.TestCase):
	def test_make_message_accepted(self):
		sample_row = ["name", "link", "inst", "Accepted"]
		message = heprumors.make_message(sample_row)
		self.assertTrue("name" in message and "inst" in message)

	def test_make_message_accepted_partial(self):
		sample_row = ["name", "link", "inst", "something Accepted something"]
		message = heprumors.make_message(sample_row)
		self.assertTrue("name" in message and "inst" in message)

	def test_make_message_offered_partial(self):
		sample_row = ["name", "link", "inst", "something offered something"]
		message = heprumors.make_message(sample_row)
		self.assertTrue("name" in message and "inst" in message)

	def test_new_records_simple(self):
		newlist = [
						["name0", "link", "inst1", "Accepted"],
						["name1 repeat", "link", "inst1", "Accepted"],
						["name2", "link", "inst2", "Accepted"],
						["name3", "link", "inst3", "Accepted"],
						["name1 repeat", "link", "inst1", "Accepted"],
						["name5 out of order", "link", "inst5", "Accepted"]
					]
		oldlist = newlist[2:5]
		updates = heprumors.new_records(oldlist, newlist)

		self.assertTrue(len(updates) == 2)
		self.assertTrue(updates[0][0] == "name0")
		self.assertTrue(updates[1][0] == "name5 out of order")

if __name__ == '__main__':
    unittest.main()
