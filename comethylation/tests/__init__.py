'''unit testing code for comethylation.
'''

import unittest
import pysam
import sys
import tempfile
import os
import re
import array

from comethylation import *

from comethylation.mtuple import *
from comethylation.funcs import *

class TestIgnoreCycles(unittest.TestCase):
	'''Test the function ignore_read_pos
	'''

	def setUp(self):

		def buildOTRead1():
			'''build an example read_1 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AATTTTAATTTTAATTTTTGCGGTATTTTTAGTCGGTTCGTTCGTTCGGGTTTGATTTGAG"
			read.flag = 99
			read.tid = 0
			read.pos = 450
			read.mapq = 255
			read.cigar = [(0,61)]
			read.rnext = 1
			read.pnext = 512
			read.tlen = 121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....")] + [("XR", "CT")]
			return read

		def buildOTRead2():
			'''build an example read_2 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AGAATTGTGTTTCGTTTTTAGAGTATTATCGAAATTTGTGTAGAGGATAACGTAGCTTC"
			read.flag = 147
			read.tid = 0
			read.pos = 512
			read.mapq = 255
			read.cigar = [(0,59)]
			read.rnext = 1
			read.pnext = 450
			read.tlen = -121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "....x....h.xZ.hh..x......hh.xZ.....x....x......h..Z.x..H.xZ")] + [("XR", "GA")]
			return read

		def buildOBRead1():
			'''build an example read_1 aligned to OB-strand
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_22929891"
			read.seq = "AACGCAACTCCGCCCTCGCGATACTCTCCGAATCTATACTAAAAAAAACGCAACTCCGCCGAC"
			read.flag = 83
			read.tid = 0
			read.pos = 560
			read.mapq = 255
			read.cigar = [(0,63)]
			read.rnext = 1
			read.pnext = 492
			read.tlen = -131
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "GA")] + [("XM", "...Z..x....Z.....Z.Zx.h......Zxh...x.h..x.hh.h...Z.......Z..Zx.")] + [("XR", "CT")]
			return read

		def buildOBRead2():
			'''build an example read_2 aligned to OB-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_22929891"
			read.seq = "CACCCGAATCTAACCTAAAAAAAACTATACTCCGCCTTCAAAATACCACCGAAATCTATACAAAAAA"
			read.flag = 163
			read.tid = 0
			read.pos = 492
			read.mapq = 255
			read.cigar = [(0,67)]
			read.rnext = 1
			read.pnext = 560
			read.tlen = 131
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "GA")] + [("XM", ".z...Zxh...x....x.hh.h....x.h....Z......x.h.......Z......x.h..x.hh.")] + [("XR", "GA")]
			return read

		# Create the reads and methylation indexes (using CpGs)
		self.otr_1 = buildOTRead1()
		self.otr_2 = buildOTRead2()
		self.obr_1 = buildOBRead1()
		self.obr_2 = buildOBRead2()
		self.otm_1 = [18, 20, 33, 38, 42, 46]
		self.otm_2 = [12, 29, 50, 58]
		self.obm_1 = [3, 11, 17, 19, 29, 49, 57, 60]
		self.obm_2 = [1, 5, 33, 50]

	def test_n_0(self):
		# Shouldn't change methylation indexes
		self.assertEqual(ignore_read_pos(self.otr_1, self.otm_1, []), [18, 20, 33, 38, 42, 46])
		self.assertEqual(ignore_read_pos(self.otr_2, self.otm_2, []), [12, 29, 50, 58])
		self.assertEqual(ignore_read_pos(self.obr_1, self.obm_1, []), [3, 11, 17, 19, 29, 49, 57, 60])
		self.assertEqual(ignore_read_pos(self.obr_2, self.obm_2, []), [1, 5, 33, 50])

	def test_n_off_by_one(self):
		# Shouldn't change methylation indexes: Ignore from "start" of read
		self.assertEqual(ignore_read_pos(self.otr_1, self.otm_1, [17]), [18, 20, 33, 38, 42, 46])
		self.assertEqual(ignore_read_pos(self.otr_2, self.otm_2, [self.otr_2.qlen - 59 - 1]), [12, 29, 50, 58])
		self.assertEqual(ignore_read_pos(self.obr_1, self.obm_1, [self.obr_1.qlen - 61 - 1]), [3, 11, 17, 19, 29, 49, 57, 60])
		self.assertEqual(ignore_read_pos(self.obr_2, self.obm_2, [0]), [1, 5, 33, 50])
		# Shouldn't change methylation indexes: Ignore from "end" of read
		self.assertEqual(ignore_read_pos(self.otr_1, self.otm_1, [47]), [18, 20, 33, 38, 42, 46])
		self.assertEqual(ignore_read_pos(self.otr_2, self.otm_2, [self.otr_2.qlen - 11 - 1]), [12, 29, 50, 58])
		self.assertEqual(ignore_read_pos(self.obr_1, self.obm_1, [self.obr_1.qlen - 2 - 1]), [3, 11, 17, 19, 29, 49, 57, 60])
		self.assertEqual(ignore_read_pos(self.obr_2, self.obm_2, [51]), [1, 5, 33, 50])

	def test_ignore_one(self):
		# Should remove one element from methylation indexes in accordance with the strand/orientation of the read
		self.assertEqual(ignore_read_pos(self.otr_1, self.otm_1, [18]), [20, 33, 38, 42, 46])
		self.assertEqual(ignore_read_pos(self.otr_2, self.otm_2, [self.otr_2.qlen - 58 - 1]), [12, 29, 50])
		self.assertEqual(ignore_read_pos(self.obr_1, self.obm_1, [self.obr_1.qlen - 60 - 1]), [3, 11, 17, 19, 29, 49, 57])
		self.assertEqual(ignore_read_pos(self.obr_2, self.obm_2, [1]), [5, 33, 50])
		# Should remove one element from methylation indexes in accordance with the strand/orientation of the read
		self.assertEqual(ignore_read_pos(self.otr_1, self.otm_1, [46]), [18, 20, 33, 38, 42])
		self.assertEqual(ignore_read_pos(self.otr_2, self.otm_2, [self.otr_2.qlen - 12 - 1]), [29, 50, 58])
		self.assertEqual(ignore_read_pos(self.obr_1, self.obm_1, [self.obr_1.qlen - 3 - 1]), [11, 17, 19, 29, 49, 57, 60])
		self.assertEqual(ignore_read_pos(self.obr_2, self.obm_2, [50]), [1, 5, 33])

	def test_ignore_all(self):
		# Should remove all elements from methylation indexes (assuming read-lengths are < 10,000)
		self.assertEqual(ignore_read_pos(self.otr_1, self.otm_1, list(range(0, 10000))), [])
		self.assertEqual(ignore_read_pos(self.otr_2, self.otm_2, list(range(0, 10000))), [])
		self.assertEqual(ignore_read_pos(self.obr_1, self.obm_1, list(range(0, 10000))), [])
		self.assertEqual(ignore_read_pos(self.obr_2, self.obm_2, list(range(0, 10000))), [])

class TestIgnoreLowQualityBases(unittest.TestCase):
	'''Test the function ignore_low_quality_bases
	'''

	def setUp(self):

		def buildPhred33():
			'''build an example read_1 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AATTTTAATTTTAATTTTTGCGGTATTTTTAGTCGGTTCGTTCGTTCGGGTTTGATTTGAG"
			read.flag = 99
			read.tid = 0
			read.pos = 450
			read.mapq = 255
			read.cigar = [(0,61)]
			read.rnext = 1
			read.pnext = 512
			read.tlen = 121
			read.qual = "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" # Phred33 = 0
			read.tags = read.tags + [("XG", "CT")] + [("XM", "..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....")] + [("XR", "CT")]
			return read

		def buildPhred64():
			'''build an example read_1 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AATTTTAATTTTAATTTTTGCGGTATTTTTAGTCGGTTCGTTCGTTCGGGTTTGATTTGAG"
			read.flag = 99
			read.tid = 0
			read.pos = 450
			read.mapq = 255
			read.cigar = [(0,61)]
			read.rnext = 1
			read.pnext = 512
			read.tlen = 121
			read.qual = "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" # Phred64 = 0
			read.tags = read.tags + [("XG", "CT")] + [("XM", "..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....")] + [("XR", "CT")]
			return read


		# Create the reads and methylation indexes (using CpGs)
		self.p33 = buildPhred33()
		self.p64 = buildPhred64()
		self.p33m = [18, 20, 33, 38, 42, 46]
		self.p64m = [18, 20, 33, 38, 42, 46]

	def test_no_low_qual_filter(self):
		# Shouldn't change methylation indexes
		self.assertEqual(ignore_low_quality_bases(self.p33, self.p33m, 0, 33), [18, 20, 33, 38, 42, 46])
		self.assertEqual(ignore_low_quality_bases(self.p64, self.p64m, 0, 64), [18, 20, 33, 38, 42, 46])

	def test_all_fail_low_qual_filter(self):
		# Should remove all elements from methylation indexes
		self.assertEqual(ignore_low_quality_bases(self.p33, self.p33m, 1, 33), [])
		self.assertEqual(ignore_low_quality_bases(self.p64, self.p64m, 1, 64), [])

	def test_some_fail_low_qual_filter(self):
		# Should remove all but the first element of the methylation index
		self.p33.qual = "!!!!!!!!!!!!!!!!!!#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" # Change one base to have Phred33 = 2
		self.p64.qual = "@@@@@@@@@@@@@@@@@@B@#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@" # Change one base to have Phred64 = 2
		self.assertEqual(ignore_low_quality_bases(self.p33, self.p33m, 2, 33), [18])
		self.assertEqual(ignore_low_quality_bases(self.p64, self.p64m, 2, 64), [18])

	def test_bad_min_qual(self):
		# Should raise an exception
		self.assertRaises(ValueError, ignore_low_quality_bases, self.p33, self.p33m, -10, 33)
		self.assertRaises(ValueError, ignore_low_quality_bases, self.p33, self.p33m, -10, 64)
		self.assertRaises(ValueError, ignore_low_quality_bases, self.p33, self.p33m, 3.4, 33)
		self.assertRaises(ValueError, ignore_low_quality_bases, self.p33, self.p33m, 3.4, 64)

	def test_bad_phred_offset(self):
		self.assertRaises(ValueError, ignore_low_quality_bases, self.p33, self.p33m, 10, 34)

class TestFixOldBismark(unittest.TestCase):
	'''Test the function fix_old_bismark
	'''

	def setUp(self):

		def buildOTRead1():
			'''build an example read_1 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AATTTTAATTTTAATTTTTGCGGTATTTTTAGTCGGTTCGTTCGTTCGGGTTTGATTTGAG"
			read.flag = 99
			read.tid = 0
			read.pos = 450
			read.mapq = 255
			read.cigar = [(0,61)]
			read.rnext = 1
			read.pnext = 512
			read.tlen = 121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			#read.tags = read.tags + [("XG", "CT")] + [("XM", "..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....")] + [("XR", "CT")] # Not required for testing fix_old_bismark
			return read

		# Create the read
		self.read = buildOTRead1()

	def test_fix_old_bismark(self):
		self.read.flag = 67
		self.assertEqual(fix_old_bismark(self.read).flag, 99)
		self.read.flag = 115
		self.assertEqual(fix_old_bismark(self.read).flag, 83)
		self.read.flag = 131
		self.assertEqual(fix_old_bismark(self.read).flag, 147)
		self.read.flag = 179
		self.assertEqual(fix_old_bismark(self.read).flag, 163)
		self.read.flag = 2
		with self.assertRaises(SystemExit) as cm:
			fix_old_bismark(self.read)
			self.assertEqual(cm.exception.code, 1)

class TestGetPositions(unittest.TestCase):
	'''Test the function get_positions.
	'''

	def setUp(self):

		def buildBasicRead(rl):
			''' Build a basic read of length rl.
			'''
			read = pysam.AlignedRead()
			read.qname = "test"
			read.seq = "A" * rl
			read.flag = 0
			read.tid = 1
			read.pos = 1
			read.mapq = 255
			read.cigar = [(0, rl)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = rl
			read.qual = "B" * rl
			return read

		def addInsertionAndDeletion(read, rpi, rpd, li, ld, f):
			'''Add insertion at rpi of length li. Add deletion at rpd of length rpd. Insertion first if f = 'i', deletion first if f = 'd'.
			WARNING: The read is updated in-place!
			'''

			if (rpi < 1 and li > 0) or (rpd < 1 and ld > 0) or rpi > len(read.seq) or rpd > len(read.seq):
				sys.exit("Can only add 'internal' indels.")

			if li > 0 and ld > 0 and f == 'i':
				nc = [(0, rpi - 1), (1, li), (0, rpd - rpi - li + 1), (2, ld), (0, read.qlen - rpd)]
			elif li > 0 and ld > 0 and f == 'd':
				nc = [(0, rpd - 1), (2, ld), (0, rpi - rpd), (1, li), (0, read.qlen - rpi - li + 1)]
			elif ld > 0:
				nc = [(0, rpd - 1), (2, ld), (0, read.qlen - rpd + 1)]
			elif li > 0:
				nc = [(0, rpi - 1), (1, li), (0, read.qlen - rpi - li + 1)]
			elif li == 0 and ld == 0:
				nc = read.cigar
			else:
				sys.exit("Incompatible parameter combination")

			read.cigar = nc
			return read

		def hardClipAndSoftClip(read, sh, eh, ss, es):
			'''Hard clip sh bases from start and eh bases from end then soft clip ss bases from start and es bases from end.
			WARNING: The read is updated in-place!
			'''

			if (sh + ss) > read.cigar[0][1] or (eh + es) > read.cigar[len(read.cigar) - 1][1]:
				sys.exit("Too much clipping; cannot clip across multiple CIGAR operations.")
			if (sh + ss + eh + es) > read.qlen:
				sys.exit("Too much clipping; sum of clipping operations cannot exceed query length.")

			q = read.qual
			oc = read.cigar
			read.seq = read.seq[sh:(len(read.seq) - eh)]
			read.qual = q[sh:(len(q) - eh)]

			n = len(oc)
			if read.cigar[0][0] != 0 or read.cigar[len(read.cigar) - 1][0] != 0 or len(read.cigar) == 2:
				sys.exit("Can only clip reads with match operations as first and last CIGAR operations.")

			nc = []
			if sh > 0:
				nc = nc + [(5, sh)]
			if ss > 0:
				nc = nc + [(4, ss)]
			if n > 2:
				nc = nc + [(oc[0][0], oc[0][1] - sh - ss)] + oc[1:(n - 1)] + [(oc[n - 1][0], oc[n - 1][1] - es - eh)]
			elif n == 1:
				nc = nc + [(oc[0][0], oc[0][1] - sh - ss - eh - es)]
			if es > 0:
				nc = nc + [(4, es)]
			if eh > 0:
				nc = nc + [(5, eh)]

			read.cigar = nc
			read.pos = read.pos + ss + sh
			return read

	# Basically, what we test test is that the output of get_positions(read) is identical to the output of read.positions with two exceptions:
	# (1) If the read contains an insertion, then compare against read.aligned_pairs, which returns None for inserted bases
	# (2) If the read contains soft-clipped bases then need to trim those "start/end Nones" from get_positions(read).

	# We test this by creating reads with a variety of indels (including no indels) and then soft-clipping and hard-clipping them in various combinations: (1) hc 2bp from start; (2) hc 1bp from end; (3) hc 2bp from start, 1bp from end; (4) sc 2bp from start; (5) sc 1bp from end; (6) sc 2bp from start, 1bp from end; (7) hc 1bp from start, hc 1bp from end, sc 1bp from start, sc 1bp from end.

		# No indels
		self.br = buildBasicRead(10)
		self.br_hcs = hardClipAndSoftClip(buildBasicRead(10), 2, 0, 0, 0)
		self.br_hce = hardClipAndSoftClip(buildBasicRead(10), 0, 1, 0, 0)
		self.br_hcse = hardClipAndSoftClip(buildBasicRead(10), 2, 1, 0, 0)
		self.br_scs = hardClipAndSoftClip(buildBasicRead(10), 0, 0, 2, 0)
		self.br_sce = hardClipAndSoftClip(buildBasicRead(10), 0, 0, 0, 1)
		self.br_scse = hardClipAndSoftClip(buildBasicRead(10), 0, 0, 2, 1)
		self.br_hcscse = hardClipAndSoftClip(buildBasicRead(10), 1, 1, 1, 1)

		# 1bp insertion
		self.I1 = addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i')
		self.I1_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 2, 0, 0, 0)
		self.I1_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 0, 1, 0, 0)
		self.I1_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 2, 1, 0, 0)
		self.I1_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 0, 0, 2, 0)
		self.I1_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 0, 0, 0, 1)
		self.I1_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 0, 0, 2, 1)
		self.I1_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 1, 0, 'i'), 1, 1, 1, 1)

		# 3bp insertion
		self.I3 = addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i')
		self.I3_hcs =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 2, 0, 0, 0)
		self.I3_hce =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 0, 1, 0, 0)
		self.I3_hcse =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 2, 1, 0, 0)
		self.I3_scs =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 0, 0, 2, 0)
		self.I3_sce =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 0, 0, 0, 1)
		self.I3_scse =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 0, 0, 2, 1)
		self.I3_hcscse =  hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 0, 3, 0, 'i'), 1, 1, 1, 1)

		# 1bp deletion
		self.D1 = addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i')
		self.D1_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 2, 0, 0, 0)
		self.D1_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 0, 1, 0, 0)
		self.D1_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 2, 1, 0, 0)
		self.D1_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 0, 0, 2, 0)
		self.D1_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 0, 0, 0, 1)
		self.D1_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 0, 0, 2, 1)
		self.D1_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 1, 'i'), 1, 1, 1, 1)

		# 3bp deletion
		self.D3 = addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i')
		self.D3_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 2, 0, 0, 0)
		self.D3_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 0, 1, 0, 0)
		self.D3_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 2, 1, 0, 0)
		self.D3_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 0, 0, 2, 0)
		self.D3_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 0, 0, 0, 1)
		self.D3_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 0, 0, 2, 1)
		self.D3_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 0, 4, 0, 3, 'i'), 1, 1, 1, 1)

		# 1bp insertion and 1bp deletion
		self.I1D1 = addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i')
		self.I1D1_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 2, 0, 0, 0)
		self.I1D1_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 0, 1, 0, 0)
		self.I1D1_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 2, 1, 0, 0)
		self.I1D1_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 0, 0, 2, 0)
		self.I1D1_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 0, 0, 0, 1)
		self.I1D1_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 0, 0, 2, 1)
		self.I1D1_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 1, 1, 'i'), 1, 1, 1, 1)

		# 2bp insertion and 3bp deletion
		self.I2D3 = addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i')
		self.I2D3_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 2, 0, 0, 0)
		self.I2D3_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 0, 1, 0, 0)
		self.I2D3_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 2, 1, 0, 0)
		self.I2D3_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 0, 0, 2, 0)
		self.I2D3_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 0, 0, 0, 1)
		self.I2D3_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 0, 0, 2, 1)
		self.I2D3_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 4, 7, 2, 3, 'i'), 1, 1, 1, 1)

		# 1bp deletion and 1bp insertion
		self.D1I1 = addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd')
		self.D1I1_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 2, 0, 0, 0)
		self.D1I1_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 0, 1, 0, 0)
		self.D1I1_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 2, 1, 0, 0)
		self.D1I1_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 0, 0, 2, 0)
		self.D1I1_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 0, 0, 0, 1)
		self.D1I1_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 0, 0, 2, 1)
		self.D1I1_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 6, 4, 1, 1, 'd'), 1, 1, 1, 1)

		# 2bp deletion and 3bp insertion
		self.D2I3 = addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd')
		self.D2I3_hcs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 2, 0, 0, 0)
		self.D2I3_hce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 0, 1, 0, 0)
		self.D2I3_hcse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 2, 1, 0, 0)
		self.D2I3_scs = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 0, 0, 2, 0)
		self.D2I3_sce = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 0, 0, 0, 1)
		self.D2I3_scse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 0, 0, 2, 1)
		self.D2I3_hcscse = hardClipAndSoftClip(addInsertionAndDeletion(buildBasicRead(10), 5, 4, 3, 2, 'd'), 1, 1, 1, 1)

	def test_no_indel(self):
		self.assertEqual(get_positions(self.br), list(range(1, 11)))
		self.assertEqual(get_positions(self.br_hcs), list(range(3, 11)))
		self.assertEqual(get_positions(self.br_hce), list(range(1, 10)))
		self.assertEqual(get_positions(self.br_hcse), list(range(3, 10)))
		self.assertEqual(get_positions(self.br_scs), [None] * 2 + list(range(3, 11)))
		self.assertEqual(get_positions(self.br_sce), list(range(1, 10)) + [None] * 1)
		self.assertEqual(get_positions(self.br_scse), [None] * 2 + list(range(3, 10)) + [None] * 1)
		self.assertEqual(get_positions(self.br_hcscse), [None] * 1 + list(range(3, 9)) + [None] * 1)

	def test_1bp_insertion(self):
		self.assertEqual(get_positions(self.I1), list(range(1, 4)) + [None] + list(range(4, 10)))
		self.assertEqual(get_positions(self.I1_hcs), list(range(3, 4)) + [None] + list(range(4, 10)))
		self.assertEqual(get_positions(self.I1_hce), list(range(1, 4)) + [None] + list(range(4, 9)))
		self.assertEqual(get_positions(self.I1_hcse), list(range(3, 4)) + [None] + list(range(4, 9)))
		self.assertEqual(get_positions(self.I1_scs), [None] * 2 + list(range(3, 4)) + [None] + list(range(4, 10)))
		self.assertEqual(get_positions(self.I1_sce), list(range(1, 4)) + [None] + list(range(4, 9)) + [None] * 1)
		self.assertEqual(get_positions(self.I1_scse), [None] * 2 + list(range(3, 4)) + [None] + list(range(4, 9)) + [None] * 1)
		self.assertEqual(get_positions(self.I1_hcscse), [None] * 1 + list(range(3, 4)) + [None] + list(range(4, 8)) + [None] * 1)

	def test_3bp_insertion(self):
		self.assertEqual(get_positions(self.I3), list(range(1, 4)) + [None] * 3 + list(range(4, 8)))
		self.assertEqual(get_positions(self.I3_hcs), list(range(3, 4)) + [None] * 3 + list(range(4, 8)))
		self.assertEqual(get_positions(self.I3_hce), list(range(1, 4)) + [None] * 3 + list(range(4, 7)))
		self.assertEqual(get_positions(self.I3_hcse), list(range(3, 4)) + [None] * 3 + list(range(4, 7)))
		self.assertEqual(get_positions(self.I3_scs), [None] * 2 + list(range(3, 4)) + [None] * 3 + list(range(4, 8)))
		self.assertEqual(get_positions(self.I3_sce), list(range(1, 4)) + [None] * 3 + list(range(4, 7)) + [None] * 1)
		self.assertEqual(get_positions(self.I3_scse), [None] * 2 + list(range(3, 4)) + [None] * 3 + list(range(4, 7)) + [None] * 1)
		self.assertEqual(get_positions(self.I3_hcscse), [None] * 1 + list(range(3, 4)) + [None] * 3 + list(range(4, 6)) + [None] * 1)

	def test_1bp_deletion(self):
		self.assertEqual(get_positions(self.D1), list(range(1, 4)) + list(range(5, 12)))
		self.assertEqual(get_positions(self.D1_hcs), list(range(3, 4)) + list(range(5, 12)))
		self.assertEqual(get_positions(self.D1_hce), list(range(1, 4)) + list(range(5, 11)))
		self.assertEqual(get_positions(self.D1_hcse), list(range(3, 4)) + list(range(5, 11)))
		self.assertEqual(get_positions(self.D1_scs), [None] * 2 + list(range(3, 4)) + list(range(5, 12)))
		self.assertEqual(get_positions(self.D1_sce), list(range(1, 4)) + list(range(5, 11)) + [None] * 1)
		self.assertEqual(get_positions(self.D1_scse), [None] * 2 + list(range(3, 4)) + list(range(5, 11)) + [None] * 1)
		self.assertEqual(get_positions(self.D1_hcscse), [None] * 1 + list(range(3, 4)) + list(range(5, 10)) + [None] * 1)

	def test_3bp_deletion(self):
		self.assertEqual(get_positions(self.D3), list(range(1, 4)) + list(range(7, 14)))
		self.assertEqual(get_positions(self.D3_hcs), list(range(3, 4)) + list(range(7, 14)))
		self.assertEqual(get_positions(self.D3_hce), list(range(1, 4)) + list(range(7, 13)))
		self.assertEqual(get_positions(self.D3_hcse), list(range(3, 4)) + list(range(7, 13)))
		self.assertEqual(get_positions(self.D3_scs), [None] * 2 + list(range(3, 4)) + list(range(7, 14)))
		self.assertEqual(get_positions(self.D3_sce), list(range(1, 4)) + list(range(7, 13)) + [None] * 1)
		self.assertEqual(get_positions(self.D3_scse), [None] * 2 + list(range(3, 4)) + list(range(7, 13)) + [None] * 1)
		self.assertEqual(get_positions(self.D3_hcscse), [None] * 1 + list(range(3, 4)) + list(range(7, 12)) + [None] * 1)

	def test_1bp_insertion_and_1bp_deletion(self):
		self.assertEqual(get_positions(self.I1D1), list(range(1, 4)) + [None] + list(range(4, 7)) + list(range(8, 11)))
		self.assertEqual(get_positions(self.I1D1_hcs), list(range(3, 4)) + [None] + list(range(4, 7)) + list(range(8, 11)))
		self.assertEqual(get_positions(self.I1D1_hce), list(range(1, 4)) + [None] + list(range(4, 7)) + list(range(8, 10)))
		self.assertEqual(get_positions(self.I1D1_hcse), list(range(3, 4)) + [None] + list(range(4, 7)) + list(range(8, 10)))
		self.assertEqual(get_positions(self.I1D1_scs), [None] * 2 + list(range(3, 4)) + [None] + list(range(4, 7)) + list(range(8, 11)))
		self.assertEqual(get_positions(self.I1D1_sce), list(range(1, 4)) + [None] + list(range(4, 7)) + list(range(8, 10)) + [None] * 1)
		self.assertEqual(get_positions(self.I1D1_scse), [None] * 2 + list(range(3, 4)) + [None] + list(range(4, 7)) + list(range(8, 10)) + [None] * 1)
		self.assertEqual(get_positions(self.I1D1_hcscse), [None] * 1 + list(range(3, 4)) + [None] + list(range(4, 7)) + list(range(8, 9)) + [None] * 1)

	def test_2bp_insertion_and_3bp_deletion(self):
		self.assertEqual(get_positions(self.I2D3), list(range(1, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 12)))
		self.assertEqual(get_positions(self.I2D3_hcs), list(range(3, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 12)))
		self.assertEqual(get_positions(self.I2D3_hce), list(range(1, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 11)))
		self.assertEqual(get_positions(self.I2D3_hcse), list(range(3, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 11)))
		self.assertEqual(get_positions(self.I2D3_scs), [None] * 2 + list(range(3, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 12)))
		self.assertEqual(get_positions(self.I2D3_sce), list(range(1, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 11)) + [None] * 1)
		self.assertEqual(get_positions(self.I2D3_scse), [None] * 2 + list(range(3, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 11)) + [None] * 1)
		self.assertEqual(get_positions(self.I2D3_hcscse), [None] * 1 + list(range(3, 4)) + [None] * 2 + list(range(4, 6)) + list(range(9, 10)) + [None] * 1)

	def test_1bp_deletion_and_1bp_insertion(self):
		self.assertEqual(get_positions(self.D1I1), list(range(1, 4)) + list(range(5, 7)) + [None] + list(range(7, 11)))
		self.assertEqual(get_positions(self.D1I1_hcs), list(range(3, 4)) + list(range(5, 7)) + [None] + list(range(7, 11)))
		self.assertEqual(get_positions(self.D1I1_hce), list(range(1, 4)) + list(range(5, 7)) + [None] + list(range(7, 10)))
		self.assertEqual(get_positions(self.D1I1_hcse), list(range(3, 4)) + list(range(5, 7)) + [None] + list(range(7, 10)))
		self.assertEqual(get_positions(self.D1I1_scs), [None] * 2 + list(range(3, 4)) + list(range(5, 7)) + [None] + list(range(7, 11)))
		self.assertEqual(get_positions(self.D1I1_sce), list(range(1, 4)) + list(range(5, 7)) + [None] + list(range(7, 10)) + [None] * 1)
		self.assertEqual(get_positions(self.D1I1_scse), [None] * 2 + list(range(3, 4)) + list(range(5, 7)) + [None] + list(range(7, 10)) + [None] * 1)
		self.assertEqual(get_positions(self.D1I1_hcscse), [None] * 1 + list(range(3, 4)) + list(range(5, 7)) + [None] + list(range(7, 9)) + [None] * 1)

	def test_2bp_deletion_and_3bp_insertion(self):
		self.assertEqual(get_positions(self.D2I3), list(range(1, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 10)))
		self.assertEqual(get_positions(self.D2I3_hcs), list(range(3, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 10)))
		self.assertEqual(get_positions(self.D2I3_hce), list(range(1, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 9)))
		self.assertEqual(get_positions(self.D2I3_hcse), list(range(3, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 9)))
		self.assertEqual(get_positions(self.D2I3_scs), [None] * 2 + list(range(3, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 10)))
		self.assertEqual(get_positions(self.D2I3_sce), list(range(1, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 9)) + [None] * 1)
		self.assertEqual(get_positions(self.D2I3_scse), [None] * 2 + list(range(3, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 9)) + [None] * 1)
		self.assertEqual(get_positions(self.D2I3_hcscse), [None] * 1 + list(range(3, 4)) + list(range(6, 7)) + [None] * 3 + list(range(7, 8)) + [None] * 1)

class TestDoesReadContainComplicatedCigar(unittest.TestCase):
	'''Test the function does_read_contain_complicated_cigar
	'''

	def setUp(self):

		def buildRead1():
			'''build an example read_1 aligned to OT-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "tr"
			read.seq = "TTTTTATTATTAAAGATAGTAGTGTTTTAAGTTTAGTGTTAGAGGTATTTGTTTGTAGTCGAAGTATTTTGTTAAAGTTAGGAGGGTTTAATAAGGTTTG"
			read.flag = 99
			read.tid = 0
			read.pos = 853
			read.mapq = 255
			read.cigar = [(0,100)]
			read.rnext = 0
			read.pnext = 854
			read.tlen = 100
			read.qual = "BBCFFBDEHH2AFHIGHIJFHIIIJJJJHHIIIJGIHHJJIJIJJDHIIIJIIJJHIJJJJJJJHIIJJJJJJGIGGJGGGFFHGFBACA@CCCCDCCD@"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "hh..h.....x........x....hh.h....h......x.....h..x...x..x..xZ....h.h.....h.....x.......h.........h.z.")] + [("XR", "CT")]
			return read

		# Create the reads
		self.read_1 = buildRead1()

	def test_simple_cigar(self):
		self.assertFalse(does_read_contain_complicated_cigar(self.read_1))

	def test_insertion(self):
		self.read_1.cigar = [(0, 50), (1, 50)]
		self.assertFalse(does_read_contain_complicated_cigar(self.read_1))

	def test_deletion(self):
		self.read_1.cigar = [(0, 50), (2, 50)]
		self.assertFalse(does_read_contain_complicated_cigar(self.read_1))

	def test_ref_skip(self):
		self.read_1.cigar = [(0, 50), (3, 50)]
		self.assertTrue(does_read_contain_complicated_cigar(self.read_1))

	def test_soft_clip(self):
		self.read_1.cigar = [(0, 50), (4, 50)]
		self.assertFalse(does_read_contain_complicated_cigar(self.read_1))

	def test_hard_clip(self):
		self.read_1.cigar = [(0, 50), (5, 50)]
		self.assertFalse(does_read_contain_complicated_cigar(self.read_1))

	def test_pad(self):
		self.read_1.cigar = [(0, 50), (6, 50)]
		self.assertTrue(does_read_contain_complicated_cigar(self.read_1))

	def test_equal(self):
		self.read_1.cigar = [(0, 50), (7, 50)]
		self.assertTrue(does_read_contain_complicated_cigar(self.read_1))

	def test_diff(self):
		self.read_1.cigar = [(0, 50), (8, 50)]
		self.assertTrue(does_read_contain_complicated_cigar(self.read_1))

class TestProcessOverlap(unittest.TestCase):
	'''Test the function process_overlap
	'''

	def setUp(self):

		def buildNoOverlapRead():
			'''build an example read-pair with methylation calls but no overlap.
			'''
			read_1 = pysam.AlignedRead()
			read_1.qname = "SRR400564.3818005_HAL:1133:C010EABXX:8:2102:8721:119200_length=101"
			read_1.seq = "TATGGGTTTGGTTTGTAGGGATTTTGTTATAAAGGTGAAATTTAGGAGAGTGTGGAGTTTAGAGTGTTGTTAGGATTTAGGTATAGGTATTAGTGTTCGTT"
			read_1.flag = 99
			read_1.tid = 0
			read_1.pos = 13546
			read_1.mapq = 30
			read_1.cigar = [(0, 101)]
			read_1.rnext = 0
			read_1.pnext = 13766
			read_1.tlen = 321
			read_1.qual = "11=BA2242323<EFGGHJJFHHIJIHIHIIJJJI?FHIIJIJIJJHIHHFHGHIDHCFHHICFCEHHIHHEHHA;?D@BCAAA>>CACADBCC#######"
			read_1.tags = read_1.tags + [('NM', 24), ('MD', '0C5C0C4C2C6C0C2C2C10C0C0C15C0C9C0C4C0C0C3C1C3C7C0C4'), ('XM', 'h.....hx....x..x......hx..h..h..........hhx...............hx.........hx....hhx...h.x...h.......hxZ...'), ('XR', 'CT'), ('XG', 'CT')]
			read_2 = pysam.AlignedRead()
			read_2.qname = "SRR400564.3818005_HAL:1133:C010EABXX:8:2102:8721:119200_length=101"
			read_2.seq = "TTTTTTATTGGGTTTTTGTAGGAGGTTGTTATTTGTTTTGTTTATTTTTTTAGAAGCGAGACGGAGTAGATTTATTTGTTATTGTTTTTTTTATAATAATT"
			read_2.flag = 147
			read_2.tid = 0
			read_2.pos = 13766
			read_2.mapq = 30
			read_2.cigar = [(0, 101)]
			read_2.rnext = 0
			read_2.pnext = 13546
			read_2.tlen = -321
			read_2.qual = "DDDDDDDDDDBDDDDDDDDDDCCDDDDDDC@9,,,,,,..C>6.,-.JJGIJJJJJJJJJJIHHHD?20001001JJJJJJJJJJJJJHHHHHFFFFFCCC"
			read_2.tags = read_2.tags + [('NM', 31), ('MD', '0C2C1C1C4C0C1C2C6C2C0C6C0C2C0C0C1C0C2C17C3C0C0C2C2C2C2C0C0C3C8C1'), ('XM', 'h..h.h.x....hh.x..x......x..hh......hx..hhh.hh..h.......Z....Z....x...hhh..x..h..x..hhh...h........h.'), ('XR', 'GA'), ('XG', 'CT')]
			return read_1, read_2

			def buildIdenticalSeqOverlap():
				'''build an example read-pair with meth calls in overlap and identical sequence in overlap.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.5201451_HAL:1133:C010EABXX:8:2108:13902:150428_length=101"
				read_1.seq = "ATAGATGTGAAGTTGAGGTTGAAGGAGATTGATGTGGTTTTTTTTTAGTTTTTTTGTGTGGTATTAGGTGGTAGTAGAGGTTAGTAAGGTAAATTTGAGTT"
				read_1.flag = 99
				read_1.tid = 0
				read_1.pos = 521475
				read_1.mapq = 11
				read_1.cigar = [(0, 101)]
				read_1.rnext = 0
				read_1.pnext = 521538
				read_1.tlen = 164
				read_1.qual = "@BCFDFFDHFFHHIJGGIHIJJJHIFGCFHIEHHEGHFHIJJJJJJIIJJIIHFDD>A5=@;ACEAC>>AB=ACC>A(+2:<AA>DCCDA@C:@A>CCBDE"
				read_1.tags = read_1.tags + [('NM', 24), ('MD', '1C10C5C9C11C1C0C1C5C1C4C2C1C0C6C2C6C2C4C3C0C0C3C0C0'), ('XM', '.x..........x.....x.........x...........h.hh.x.....h.x....z..h.hx......x..x......x..h....h...hxz...hx'), ('XR', 'CT'), ('XG', 'CT')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.5201451_HAL:1133:C010EABXX:8:2108:13902:150428_length=101"
				read_2.seq = "TTAGGTGGTAGTAGAGGTTAGTAAGGTAAATTTGAGTTTGGGGATGTGGGGTGGGGGTAGTTATATTTTTTTTTGAGTTATAGTAGATTTATTTTGTTTTG"
				read_2.flag = 147
				read_2.tid = 0
				read_2.pos = 521538
				read_2.mapq = 11
				read_2.cigar = [(0, 101)]
				read_2.rnext = 0
				read_2.pnext = 521475
				read_2.tlen = -164
				read_2.qual = "@CDDDDDDDCCCCDD@CCACCDDDDEDDDDDDDCDDDDDDDEEEDDFFHHEJJIHIJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJHHHHHFFFFFCCC"
				read_2.tags = read_2.tags + [('NM', 29), ('MD', '0C0C6C2C6C2C4C3C0C0C3C0C0C7C10C2C2C0G1C0C1C1C5C2C2C5C1C1C4C2'), ('XM', 'hx......x..x......x..h....h...hxz...hxz.......z..........x..h..z..hh.h.h.....h..x..x.....h.h.x....x..'), ('XR', 'GA'), ('XG', 'CT')]
				return read_1, read_2

			def buildIdenticalXMDifferentSeqOverlap():
				'''build an example read-pair with meth calls in overlap and identical XM but different sequence in overlap.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.71_HAL:1133:C010EABXX:8:1101:1825:2253_length=101"
				read_1.seq = "CCCCCACTAAACGCATAACCTCTATACCTAAACTCACACCTAAAAAACAACGTCTCTCCTCTCNCTACACAATACTACGAAATTACTATTACAAANNATAA"
				read_1.flag = 83
				read_1.tid = 9
				read_1.pos = 91057649
				read_1.mapq = 24
				read_1.cigar = [(0, 101)]
				read_1.rnext = 9
				read_1.pnext = 91057589
				read_1.tlen = -161
				read_1.qual = "66<<;<:9:<<<==<=<??>=>==>??>=>?>?=?????;>???????????<???=??<?<1#>>?>?:@@>?@?@@@@@???@?>@??@?@<2##@<<<"
				read_1.tags = read_1.tags + [('NM', 23), ('MD', '8G0G6G0G5G1G4G0G12G4G13T2G4G1G2G2G0G0G2G8G1G0A2G1'), ('XM', '........xh..Z...hh.....x.h....hh............h....x.Z..............x....x.h..x.Zxhh..h........x.....h.'), ('XR', 'CT'), ('XG', 'GA')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.71_HAL:1133:C010EABXX:8:1101:1825:2253_length=101"
				read_2.seq = "NAAAAGCTAAAACAAAAAAACNAAATNNNNGCCTATCTAATACTATAAATAATAACTNNNCNCCCACTAAACGCATAACCTCTATACCTAAACTNNCACCT"
				read_2.flag = 163
				read_2.tid = 9
				read_2.pos = 91057589
				read_2.mapq = 24
				read_2.cigar = [(0, 101)]
				read_2.rnext = 9
				read_2.pnext = 91057649
				read_2.tlen = 161
				read_2.qual = "#1=DFFFFHGHHHJJIJJJJJ#1?FH####00?FHIJJIJJJJJJJJJJJHJJJJJI###-#,,?BDEEEDCDDDDBDDDDDDDDEDDDDDDDD##++8??"
				read_2.tags = read_2.tags + [('NM', 41), ('MD', '0C1G1G3G0G0G0G2G0G0G2G1C1G2G0G0C0C4G3G0G1G2G1G1G1G0G1G3G0C0A1C6G0G6G0G5G1G4G0G2C0A5'), ('XM', '..x.hH..xhhh..xhh..h...x......Z...x...xh.h..x.h.h.hh.h..............xh..Z...hh.....x.h....hh.........'), ('XR', 'GA'), ('XG', 'GA')]
				return read_1, read_2

			def buildSmallXMDifferenceOverlap():
				'''build an example read-pair with meth calls in overlap but slightly different XM-tags in overlap.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.9511_HAL:1133:C010EABXX:8:1101:20403:11881_length=101"
				read_1.seq = "ATAATTTTTACATCTTTTATAAAAAAAATAATCTCGAAAAACTAAAATTACAAACGACTACCACCACGCCCGACTAATTTTTACATTTTTAATAAAAACGA"
				read_1.flag = 83
				read_1.tid = 8
				read_1.pos = 131548740
				read_1.mapq = 40
				read_1.cigar = [(0, 101)]
				read_1.rnext = 8
				read_1.pnext = 131548707
				read_1.tlen = -134
				read_1.qual = "##################@?@B@@@;;((>1551=6=;)..);7;;=7.(;@5-')))=@168?:@AAFC2FA3HCCEH@AC<<EEIIFFFHDDDA44111"
				read_1.tags = read_1.tags + [('NM', 22), ('MD', '0C17G4G2G0G9G0G1G2G0G0G6G0G2C2G12G9G7G0G2G1G3G0'), ('XM', '..................h....h..hh.......Z.hh.h..xhh......xh.Z...x.......Z...Zx.........h.......hh..h.h..Zx'), ('XR', 'CT'), ('XG', 'GA')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.9511_HAL:1133:C010EABXX:8:1101:20403:11881_length=101"
				read_2.seq = "ACAAACGTAAACCACCACGCCCGACCTACTCAACTAATTTTTACATCTTTTATAAAAAAAATAATCTCGAAAAACTAAAATTACAAACGCCTACCACCACA"
				read_2.flag = 163
				read_2.tid = 8
				read_2.pos = 131548707
				read_2.mapq = 40
				read_2.cigar = [(0, 101)]
				read_2.rnext = 8
				read_2.pnext = 131548740
				read_2.tlen = 134
				read_2.qual = "@B@FFFFDFHHHHJJJJJGJJJIIJJIJJJJJJJJIJJJJJJIJJJJJIHCFIGHIGIHFDDDDEDCDDDDDDDDDDDDDDCCCCCDA>>@?>?AACBA<2"
				read_2.tags = read_2.tags + [('NM', 19), ('MD', '3G0G3G1G12G27G4G2G0G9G0G1G2G0G0G6G0G5G7G0'), ('XM', '...xh.Z.h.h.......Z...Zx...........................h....h..hh.......Z.hh.h..xhh......xh.Z...x.......z'), ('XR', 'GA'), ('XG', 'GA')]
				return read_1, read_2

			def buildLargeXMDifferenceOverlap():
				'''build an example read-pair with meth calls in overlap but very different XM-tags in overlap.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.671_HAL:1133:C010EABXX:8:1101:10776:2987_length=101"
				read_1.seq = "TTGGTTTGTGTGGGAGGATTTTGTTATGGTAAGTAAGAGAGAGGTCGCGTGTGCGTGTGCGTGTGTAGGTGTTTTTGTGTGTGGAAGTAGTGTGGATTATT"
				read_1.flag = 99
				read_1.tid = 8
				read_1.pos = 37918311
				read_1.mapq = 23
				read_1.cigar = [(0, 101)]
				read_1.rnext = 8
				read_1.pnext = 37918347
				read_1.tlen = 136
				read_1.qual = "=@?=ABDAACFDFHGGHFGIIJJJJIIIIDGGGFHGGDGHGGGHBFHIIFHGHHHEBBDC<AA;?A@CC:@A@CDBBBCCBAB@>:>44>>?:@B3>A###"
				read_1.tags = read_1.tags + [('NM', 14), ('MD', '0C3C0C12C0C0C2C5C3C39C13C8C0C1C1'), ('XM', 'x...hx............hhx..h.....h...h...........Z.Z.....Z.....Z.............h.............x........hh.x.'), ('XR', 'CT'), ('XG', 'CT')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.671_HAL:1133:C010EABXX:8:1101:10776:2987_length=101"
				read_2.seq = "GAGGAGAGGGTGTGTGTGTGTGTGTGTGTGTAGGTGTTTTTGTGTGTGGAAGTAGTGTGGATTATTGAGGGTTGTGTGTGTGTGTGTGTGTGTGTGTAGGT"
				read_2.flag = 147
				read_2.tid = 8
				read_2.pos = 37918347
				read_2.mapq = 23
				read_2.cigar = [(0, 4), (1, 1), (0, 96)]
				read_2.rnext = 8
				read_2.pnext = 37918311
				read_2.tlen = -136
				read_2.qual = "###########@8DDDDB?DDDB@8DDDDC>;?B?BDADDFFFHHHHC@@@GDGHGHGGAGFFEHAAEIHGDEGIIGJJJJJJJJJJJHHGHHFFFFFCCC"
				read_2.tags = read_2.tags + [('NM', 13), ('MD', '3A4T0C1C5C5C13C13C8C0C1C6C29'), ('XM', '..........z.z.....z.....z.............h.............x........hh.x......x.............................'), ('XR', 'GA'), ('XG', 'CT')]
				return read_1, read_2

			def buildInsertionOutsideOfOverlap():
				'''build an example read-pair with meth calls in overlap and an insertion outside of the overlap in both reads. Note the sequence is identical in the overlap.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.41106_HAL:1133:C010EABXX:8:1101:16059:44833_length=101"
				read_1.seq = "AAAAAACTCAACAAAACACCAACAACTCACAAAACAATACATTTTCTTAACTTTCTAACAATACAAAATCATTGTTCAATAAAATTTACATATACACCTTA"
				read_1.flag = 83
				read_1.tid = 13
				read_1.pos = 65347555
				read_1.mapq = 0
				read_1.cigar = [(0, 62), (1, 1), (0, 38)]
				read_1.rnext = 13
				read_1.pnext = 65347514
				read_1.tlen = -141
				read_1.qual = "DDDECCA@AFDBFFHFEDHGHHGFF@@GHGIIIIIIGIGGIIHIGGIIIHIIIIIIIIIIHHF?IIHHBAIIIIIIIIIIIIIIIIIHHHFHHDAA1D@??"
				read_1.tags = read_1.tags + [('NM', 24), ('MD', '0G1G8T1G6G0G2G2T0G3G0G2G11G10G5G0G10G3G0G5G1G3G4G0'), ('XM', 'h.h..........h......zx..x...h...hh..x...........h..........z......hh.....H....x...hh.....z.h...z....h'), ('XR', 'CT'), ('XG', 'GA')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.41106_HAL:1133:C010EABXX:8:1101:16059:44833_length=101"
				read_2.seq = "AACCAATAATACCAAAAAAACATCTCCAAATTACCCCCAAAAAAAAAACTCAACAAAACACCAACAACTCACAAAACAATACATTTTCTTAACTTTCTAAC"
				read_2.flag = 163
				read_2.tid = 13
				read_2.pos = 65347514
				read_2.mapq = 0
				read_2.cigar = [(0, 38), (1, 1), (0, 62)]
				read_2.rnext = 13
				read_2.pnext = 65347555
				read_2.tlen = 141
				read_2.qual = "CCCFFFFFHHHHHJJJIJJJJJJJJJJIJJJJJJJJJJJJJJJJJHFDDC@CDCDDDDABABDD@BDBDCC?CDDDBDDCCCDEEEE@CDCE@CCCCDDE>"
				read_2.tags = read_2.tags + [('NM', 25), ('MD', '4G2G0G1G7G0G7G1G2G5G0G1G1G8T1G6G0G2G2T0G3G0G2G11G10'), ('XM', '....z..hh.h.......hh.......z.h..h......xh.h.h..........h......zx..x...h...hh..x...........h..........'), ('XR', 'GA'), ('XG', 'GA')]
				return read_1, read_2

			def buildIndelicious():
				'''build an example read-pair with meth calls in overlap, where an insertion means that seq (and XM) aren't identical between reads but they are at positions in common.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.5403_HAL:1133:C010EABXX:8:1101:1870:7806_length=101"
				read_1.seq = "AAACATATTCTTAATCTTCATAATTCCCTCATCCTCCCTAAAATCAAATCCGAATCAACCACCTTCGATATATTCCAACAAAAACCTCTCCCTCTACCCTA"
				read_1.flag = 83
				read_1.tid = 4
				read_1.pos = 3090709
				read_1.mapq = 3
				read_1.cigar = [(0, 101)]
				read_1.rnext = 4
				read_1.pnext = 3090675
				read_1.tlen = -135
				read_1.qual = "ADDCC@C@CCCCCCAAACCC@CA??BCC@CA;A=;6?>AHHHEADGHHCJJJIHCGIHFB?IIGGGIIGHDHHGJIJIJJIIHGIHFHDFFDFA=2AD@=="
				read_1.tags = read_1.tags + [('NM', 16), ('MD', '0C5G6G7G17G0G0G10G4G9G1G1G5G2G0G18G0'), ('XM', '......h......h.......h.................xhh.........Zx....x........Zx.h.h.....x..xh..................x'), ('XR', 'CT'), ('XG', 'GA')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.5403_HAL:1133:C010EABXX:8:1101:1870:7806_length=101"
				read_2.seq = "CTTCCGATATTATCTAAAAAAATCTCTCACATACCAACTAAACATATTCTTAATCTTCATAATTCCCTCATCCTCCCTAAAATCAAATCCGAATCAACCAC"
				read_2.flag = 163
				read_2.tid = 4
				read_2.pos = 3090675
				read_2.mapq = 3
				read_2.cigar = [(0, 35), (1, 5), (0, 61)]
				read_2.rnext = 4
				read_2.pnext = 3090709
				read_2.tlen = 135
				read_2.qual = "CCCFFFFFHHHGHIJIJJIJJJJJJJJJJJJJIJJJIJJIIIJJJJJJHJFHIJHIJJIJIDHH?CHHHFFFFFFEDEEDCDEDDDDDDCDDDDBCDDABD"
				read_2.tags = read_2.tags + [('NM', 21), ('MD', '6G1G2G3G0G0G2G11G7G6G7G17G0G0G10G4G4'), ('XM', '.....Zx.h..h...xhh..h...........h............h......h.......h.................xhh.........Zx....x....'), ('XR', 'GA'), ('XG', 'GA')]
				return read_1, read_2

			def buildDelAtEndOfOverlap():
				'''build an example read-pair with meth calls in overlap, where a deletion at the end of the overlap coincides with a CpG, which means the overlap is particularly difficult to calculate.
				'''
				read_1 = pysam.AlignedRead()
				read_1.qname = "SRR400564.2497275_HAL:1133:C010EABXX:8:1204:20661:123404_length=101"
				read_1.seq = "CATCAACACCACCCATCTAAAACCCAAAAAAAAAAACTTTCCCTCTATCCCCCAACCTTTAAACTATCACCAAACAAACCATTCATTCATCAAATACTTTT"
				read_1.flag = 83
				read_1.tid = 7
				read_1.pos = 12294957
				read_1.mapq = 7
				read_1.cigar = [(0, 25), (2, 1), (0, 76)]
				read_1.rnext = 7
				read_1.pnext = 12294882
				read_1.tlen = -177
				read_1.qual = "###########?@::43<DB??<5-@DDDDDFFED@FFFDHIIEGIGFJJJJIIFIIIJIIIFF??@F?JJIHHGJJJJJIJJIJIJJHGHHHDB=4FCBB"
				read_1.tags = read_1.tags + [('NM', 21), ('MD', '5G1G6G3G0G0G0G3^G3G0G1G0G0G1G10G7G5G0G3G11G6G16'), ('XM', '.....x.z......z...xhhh......hh.hhh.h..........x.......x.....hh...x...........h......z................'), ('XR', 'CT'), ('XG', 'GA')]
				read_2 = pysam.AlignedRead()
				read_2.qname = "SRR400564.2497275_HAL:1133:C010EABXX:8:1204:20661:123404_length=101"
				read_2.seq = "TTCAAAAAAATCTTTTCAACAAAAACCTTACAAATACATACTTCAATCCTAAAAACCTTATCCTAACCTCCTCTCCATCAACACCACCCATCTAAAACCCA"
				read_2.flag = 163
				read_2.tid = 7
				read_2.pos = 12294882
				read_2.mapq = 7
				read_2.cigar = [(0, 101)]
				read_2.rnext = 7
				read_2.pnext = 12294957
				read_2.tlen = 177
				read_2.qual = "BBCFFFFFHGHFHJJJJJJJIJIJJJIJIHGHGHGHJIIJJJJJIIIJJJCGIIJIGHIIJJIHHHHGHFFFFEEEEEEDDDDDDBDDDDDDDDDDDDDD?"
				read_2.tags = read_2.tags + [('NM', 29), ('MD', '4G0G2G0G8G2G0G0G0G6G0G0G1G3G4G0G4G0G1G0G10G14G1G6G3G0G0G0G3G0'), ('XM', '....xh..hh........x..xhhh......zxh.h...h....zx....xh.hh..........h..............x.z......z...xhhh...z'), ('XR', 'GA'), ('XG', 'GA')]
				return read_1, read_2

			# Create the reads, methylation indexes and FAILED_QC file
			# There are the methylation indexes, where x indicates those in an overlap
			# nor: ([97], [56, 61])
			# iso: ([58, 95x], [32x, 38, 46, 63])
			# ixmdso: ([12x, 51, 78], [30x, 72])
			# sxmdo: ([35x, 55x, 67x, 71, 99], [6, 18, 22, 68x, 88x, 100x])
			# lxmdo: ([45x, 47x, 53x, 59x], [10x, 12x, 18x, 24x])
			# iooo: ([20x, 59, 89, 95], [4, 27, 62x])
			# i: ([51x, 66], [5, 90x])
			self.methylation = re.compile(r'[Zz]')
			self.nor_1, self.nor_2 = buildNoOverlapRead()
			self.nor_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.nor_1.opt('XM'))]
			self.nor_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.nor_2.opt('XM'))]
			self.iso_1, self.iso_2 = buildIdenticalSeqOverlap()
			self.iso_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.iso_1.opt('XM'))]
			self.iso_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.iso_2.opt('XM'))]
			self.ixmdso_1, self.ixmdso_2 = buildIdenticalXMDifferentSeqOverlap()
			self.ixmdso_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.ixmdso_1.opt('XM'))]
			self.ixmdso_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.ixmdso_2.opt('XM'))]
			self.sxmdo_1, self.sxmdo_2 = buildSmallXMDifferenceOverlap()
			self.sxmdo_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.sxmdo_1.opt('XM'))]
			self.sxmdo_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.sxmdo_2.opt('XM'))]
			self.lxmdo_1, self.lxmdo_2 = buildLargeXMDifferenceOverlap()
			self.lxmdo_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.lxmdo_1.opt('XM'))]
			self.lxmdo_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.lxmdo_2.opt('XM'))]
			self.iooo_1, self.iooo_2 = buildInsertionOutsideOfOverlap()
			self.iooo_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.iooo_1.opt('XM'))]
			self.iooo_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.iooo_2.opt('XM'))]
			self.i_1, self.i_2 = buildIndelicious()
			self.i_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.i_1.opt('XM'))]
			self.i_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.i_2.opt('XM'))]
			self.daeoo_1, self.daeoo_2 = buildDelAtEndOfOverlap()
			self.daeoo_mi_1 = [midx.start() for midx in re.finditer(methylation_pattern, self.daeoo_1.opt('XM'))]
			self.daeoo_mi_2 = [midx.start() for midx in re.finditer(methylation_pattern, self.daeoo_2.opt('XM'))]
			self.FAILED_QC = open(tempfile.mkstemp()[1], 'w')

		def test_sequence_strict_overlap_check(self):
			overlap_check = "sequence_strict"
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, ixmdso_mi_1, ixmdso_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))

		def test_sequence_overlap_check(self):
			overlap_check = "sequence"
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, ixmdso_mi_1, ixmdso_mi_2, overlap_check, self.FAILED_QC), ([51, 78], [72], 0))
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([71, 99], [6, 18, 22], 0))
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 0))
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([66], [5], 0))
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([84], [31, 44], 0))

		def test_XM_strict_overlap_check(self):
			overlap_check = "XM_strict"
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, ixmdso_mi_1, ixmdso_mi_2, overlap_check, self.FAILED_QC), ([12, 51, 78], [72], 0))
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([51, 66], [5], 0))
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([], [], 1))

		def test_XM_overlap_check(self):
			overlap_check = "XM"
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, ixmdso_mi_1, ixmdso_mi_2, overlap_check, self.FAILED_QC), ([12, 51, 78], [72], 0))
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([71, 99], [6, 18, 22], 0))
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 0))
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([51, 66], [5], 0))
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([84], [31, 44], 0))

		def test_XM_ol_overlap_check(self):
			overlap_check = "XM_ol"
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, ixmdso_mi_1, ixmdso_mi_2, overlap_check, self.FAILED_QC), ([12, 51, 78], [72], 0))
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([35, 55, 71, 99], [6, 18, 22], 0))
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [], 0))
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([51, 66], [5], 0))
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([7, 14, 84], [31, 44, 82, 89], 0))

		def test_quality_overlap_check(self):
			# Fudge quality scores to test overlap_check = 'quality'.
			self.nor_1.qual = 'G' * len(self.nor_1.seq)
			self.nor_2.qual = 'F' * len(self.nor_2.seq)
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.nor_1.qual = 'E' * len(self.nor_1.seq)
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.iso_1.qual = 'G' * len(self.iso_1.seq)
			self.iso_2.qual = 'F' * len(self.iso_2.seq)
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.iso_1.qual = 'E' * len(self.iso_1.seq)
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58], [32, 38, 46, 63], 0))
			self.ixmdso_1.qual = 'G' * len(self.ixmdso_1.seq)
			self.ixmdso_2.qual = 'F' * len(self.ixmdso_2.seq)
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, self.ixmdso_mi_1, self.ixmdso_mi_2, overlap_check, self.FAILED_QC), ([12, 51, 78], [72], 0))
			self.ixmdso_1.qual = 'E' * len(self.ixmdso_1.seq)
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, self.ixmdso_mi_1, self.ixmdso_mi_2, overlap_check, self.FAILED_QC), ([51, 78], [30, 72], 0))
			self.sxmdo_1.qual = 'G' * len(self.sxmdo_1.seq)
			self.sxmdo_2.qual = 'F' * len(self.sxmdo_2.seq)
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([35, 55, 67, 71, 99], [6, 18, 22], 0))
			self.sxmdo_1.qual = 'E' * len(self.sxmdo_1.seq)
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([71, 99], [6, 18, 22, 68, 88, 100], 0))
			self.lxmdo_1.qual = 'G' * len(self.lxmdo_1.seq)
			self.lxmdo_2.qual = 'F' * len(self.lxmdo_2.seq)
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([45, 47, 53, 59], [], 0))
			self.lxmdo_1.qual = 'E' * len(self.lxmdo_1.seq)
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([], [10, 12, 18, 24], 0))
			self.iooo_1.qual = 'G' * len(self.iooo_1.seq)
			self.iooo_2.qual = 'F' * len(self.iooo_2.seq)
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.iooo_1.qual = 'E' * len(self.iooo_1.seq)
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([59, 89, 95], [4, 27, 62], 0))
			self.i_1.qual = 'G' * len(self.i_1.seq)
			self.i_2.qual = 'F' * len(self.i_2.seq)
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([51, 66], [5], 0))
			self.i_1.qual = 'E' * len(self.i_1.seq)
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([66], [5, 90], 0))
			self.daeoo_1.qual = 'G' * len(self.daeoo_1.seq)
			self.daeoo_2.qual = 'F' * len(self.daeoo_2.seq)
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([7, 14, 84], [31, 44], 0))
			self.daeoo_1.qual = 'E' * len(self.daeoo_1.seq)
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([84], [31, 44, 82, 89], 0))

		def test_Bismark_overlap_check(self):
			overlap_check = "Bismark"
			self.assertEqual(process_overlap(self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, overlap_check, self.FAILED_QC), ([97], [56, 61], 0))
			self.assertEqual(process_overlap(self.iso_1, self.iso_2, self.iso_mi_1, self.iso_mi_2, overlap_check, self.FAILED_QC), ([58, 95], [38, 46, 63], 0))
			self.assertEqual(process_overlap(self.ixmdso_1, self.ixmdso_2, ixmdso_mi_1, ixmdso_mi_2, overlap_check, self.FAILED_QC), ([12, 51, 78], [72], 0))
			self.assertEqual(process_overlap(self.sxmdo_1, self.sxmdo_2, self.sxmdo_mi_1, self.sxmdo_mi_2, overlap_check, self.FAILED_QC), ([35, 55, 67, 71, 99], [6, 18, 22], 0))
			self.assertEqual(process_overlap(self.lxmdo_1, self.lxmdo_2, self.lxmdo_mi_1, self.lxmdo_mi_2, overlap_check, self.FAILED_QC), ([45, 47, 53, 59], [], 0))
			self.assertEqual(process_overlap(self.iooo_1, self.iooo_2, self.iooo_mi_1, self.iooo_mi_2, overlap_check, self.FAILED_QC), ([20, 59, 89, 95], [4, 27], 0))
			self.assertEqual(process_overlap(self.i_1, self.i_2, self.i_mi_1, self.i_mi_2, overlap_check, self.FAILED_QC), ([51, 66], [5], 0))
			self.assertEqual(process_overlap(self.daeoo_1, self.daeoo_2, self.daeoo_mi_1, self.daeoo_mi_2, overlap_check, self.FAILED_QC), ([7, 14, 84], [31, 44], 0))

			def test_bad_overlap_check(self):
				self.assertRaises(ValueError, process_overlap, self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, "bismark", self.FAILED_QC)
				self.assertRaises(ValueError, process_overlap, self.nor_1, self.nor_2, self.nor_mi_1, self.nor_mi_2, "seq", self.FAILED_QC)

class TestExtractAndUpdateMethylationIndexFromSingleEndRead(unittest.TestCase):
	'''Test the function extract_and_update_methylation_index_from_single_end_read
	'''
	def setUp(self):

		def buildOTRead():
			'''build an example read aligned to OT-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "@SALK_2077_FC6295TAAXX:2:107:9396:15019#0/1"
			read.seq = "GGGGAAGGTGTTATGGAGTTTTTTACGATTTTTAGTCGTTTTCGTTTTTTTTTGTTTGTGGTTGTTGCGGTGGCGGTAGAGGAGGG"
			read.flag = 0
			read.tid = 0
			read.pos = 4536
			read.mapq = 255
			read.cigar = [(0,86)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "DBDB2;@>)@@F?EFG@GBGGGGDDBG@DGGGGEEFHHEGHHHHEFHHHHFHHHFHHHGHGBCEAA@?@?/A@>@3,.6,AA,@>="
			read.tags = read.tags + [("XG", "CT")] + [("XM", "...........h......hhhhh..Z....hhx...Z..hh.Z..hh.hh.x..hx.....x..x..Z.....Z..x.........")] + [("XR", "CT")]
			return read

		def buildOBRead():
			'''build an example read aligned to OB-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "@ECKER_1116_FC623CNAAXX:2:21:18515:1127#0/1"
			read.seq = "CTTCCTAACAAACAACTACACCACTACCTAACGCTATACCCTTCCTTTACTCTACCCACTAAAAACAATATTTATCATAAACCT"
			read.flag = 16
			read.tid = 0
			read.pos = 3334
			read.mapq = 255
			read.cigar = [(0,84)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "G7@G@BGB@GGGGGDIEEBIBA<AHEGEEEGGGDDEDFFEIIHIIGGDGGGGGGGGGGDGDBED<FAAFEGGGGGIHIFIGBDG"
			read.tags = read.tags + [("XG", "GA")] + [("XM", "......x...xh..x..x.......x...xh.Z..x.h..........h....x...z..xh.h..zx.h...h....hhh...")] + [("XR", "CT")]
			return read

		def buildBAM():
			'''build a BAM file
			'''
			header = { 'HD': {'VN': '1.0'}, 'SQ': [{'LN': 10000, 'SN': 'chr1'}, {'LN': 20000, 'SN': 'chr2'}] }
			tempfile_path = tempfile.mkstemp()[1]
			BAM = pysam.Samfile(tempfile_path, "wb", header = header)
			return BAM

		# Create the reads, BAM file and methylation m-tuples
		self.otr = buildOTRead()
		self.obr = buildOBRead()
		self.BAM = buildBAM()
		self.BAM.write(self.otr)
		self.BAM.write(self.obr)
		self.filename = self.BAM.filename
		self.BAM.close()
		self.BAM = pysam.Samfile(self.filename, 'rb')
		self.m1ot, self.nmlifot = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m1otac, self.nmlifotac = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m2ot, self.nmlifot = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2,  methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m2otac, self.nmlifotac = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2,  methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m3ot, self.nmlifot = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m3otac, self.nmlifotac = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m4ot, self.nmlifot = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 4, 'CG', {'chr1': 0}), m = 4, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m4otac, self.nmlifotac = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 4, 'CG', {'chr1': 0}), m = 4, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m5ot, self.nmlifot = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 5, 'CG', {'chr1': 0}), m = 5, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m5otac, self.nmlifotac = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 5, 'CG', {'chr1': 0}), m = 5, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m1ob, self.nmlifob = extract_and_update_methylation_index_from_single_end_read(read = self.obr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m1obac, self.nmlifobac = extract_and_update_methylation_index_from_single_end_read(read = self.obr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m2ob, self.nmlifob = extract_and_update_methylation_index_from_single_end_read(read = self.obr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m2obac, self.nmlifobac = extract_and_update_methylation_index_from_single_end_read(read = self.obr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m3ob, self.nmlifob = extract_and_update_methylation_index_from_single_end_read(read = self.obr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m3obac, self.nmlifobac = extract_and_update_methylation_index_from_single_end_read(read = self.obr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1)
		self.m2cgchg, self.nmlifotcgchg = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG/CHG', {'chr1': 0}), m = 2, all_combinations = False, methylation_type = 'CG/CHG', methylation_pattern = re.compile(r'[ZzXx]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 0)
		self.m2cgchgac, self.nmlifotcgchgac = extract_and_update_methylation_index_from_single_end_read(read = self.otr, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG/CHG', {'chr1': 0}), m = 2, all_combinations = True, methylation_type = 'CG/CHG', methylation_pattern = re.compile(r'[ZzXx]'), ignore_read_1_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 0)

	def test_correct_number_of_m_tuples(self):
		self.assertEqual(len(self.m1ot.mtuples), 5)
		self.assertEqual(len(self.m1otac.mtuples), 5)
		self.assertEqual(len(self.m2ot.mtuples), 4)
		self.assertEqual(len(self.m2otac.mtuples), 10)
		self.assertEqual(len(self.m3ot.mtuples), 3)
		self.assertEqual(len(self.m3otac.mtuples), 10)
		self.assertEqual(len(self.m4ot.mtuples), 2)
		self.assertEqual(len(self.m4otac.mtuples), 5)
		self.assertEqual(len(self.m5ot.mtuples), 1)
		self.assertEqual(len(self.m5otac.mtuples), 1)
		self.assertEqual(len(self.m1ob.mtuples), 3)
		self.assertEqual(len(self.m1obac.mtuples), 3)
		self.assertEqual(len(self.m2ob.mtuples), 2)
		self.assertEqual(len(self.m2obac.mtuples), 3)
		self.assertEqual(len(self.m3ob.mtuples), 1)
		self.assertEqual(len(self.m3obac.mtuples), 1)
		self.assertEqual(len(self.m2cgchg.mtuples), 10)
		self.assertEqual(len(self.m2cgchgac.mtuples), 55)

	def test_correct_m_tuple_ids(self):
		# Can't use assertItemsEqual because it is renamed assertCountEqual in Python 3.
		# Instead use assertEqual(sorted(expected), sorted(actual))
		self.assertEqual(sorted(list(self.m1ot.mtuples.keys())), sorted([('chr1', '*', 4562), ('chr1', '*', 4604), ('chr1', '*', 4579), ('chr1', '*', 4573), ('chr1', '*', 4610)]))
		self.assertEqual(sorted(list(self.m1otac.mtuples.keys())), sorted([('chr1', '*', 4562), ('chr1', '*', 4604), ('chr1', '*', 4579), ('chr1', '*', 4573), ('chr1', '*', 4610)]))
		self.assertEqual(sorted(list(self.m2ot.mtuples.keys())), sorted([('chr1', '*', 4579, 4604), ('chr1', '*', 4562, 4573), ('chr1', '*', 4604, 4610), ('chr1', '*', 4573, 4579)]))
		self.assertEqual(sorted(list(self.m2otac.mtuples.keys())), sorted([('chr1', '*', 4562, 4573), ('chr1', '*', 4562, 4579), ('chr1', '*', 4562, 4604), ('chr1', '*', 4562, 4610), ('chr1', '*', 4573, 4579), ('chr1', '*', 4573, 4604), ('chr1', '*', 4573, 4610), ('chr1', '*', 4579, 4604), ('chr1', '*', 4579, 4610), ('chr1', '*', 4604, 4610)]))
		self.assertEqual(sorted(list(self.m3ot.mtuples.keys())), sorted([('chr1', '*', 4562, 4573, 4579), ('chr1', '*', 4573, 4579, 4604), ('chr1', '*', 4579, 4604, 4610)]))
		self.assertEqual(sorted(list(self.m3otac.mtuples.keys())), sorted([('chr1', '*', 4562, 4579, 4610), ('chr1', '*', 4562, 4604, 4610), ('chr1', '*', 4573, 4579, 4604), ('chr1', '*', 4573, 4579, 4610), ('chr1', '*', 4573, 4604, 4610), ('chr1', '*', 4579, 4604, 4610), ('chr1', '*', 4562, 4573, 4579), ('chr1', '*', 4562, 4573, 4604), ('chr1', '*', 4562, 4573, 4610), ('chr1', '*', 4562, 4579, 4604)]))
		self.assertEqual(sorted(list(self.m4ot.mtuples.keys())), sorted([('chr1', '*', 4562, 4573, 4579, 4604), ('chr1', '*', 4573, 4579, 4604, 4610)]))
		self.assertEqual(sorted(list(self.m4otac.mtuples.keys())), sorted([('chr1', '*', 4562, 4573, 4579, 4604), ('chr1', '*', 4573, 4579, 4604, 4610), ('chr1', '*', 4562, 4573, 4604, 4610), ('chr1', '*', 4562, 4573, 4579, 4610), ('chr1', '*', 4562, 4579, 4604, 4610)]))
		self.assertEqual(sorted(list(self.m5ot.mtuples.keys())), sorted([('chr1', '*', 4562, 4573, 4579, 4604, 4610)]))
		self.assertEqual(sorted(list(self.m5otac.mtuples.keys())), sorted([('chr1', '*', 4562, 4573, 4579, 4604, 4610)]))
		self.assertEqual(sorted(list(self.m1ob.mtuples.keys())), sorted([('chr1', '*', 3400), ('chr1', '*', 3366), ('chr1', '*', 3391)]))
		self.assertEqual(sorted(list(self.m1obac.mtuples.keys())), sorted([('chr1', '*', 3400), ('chr1', '*', 3366), ('chr1', '*', 3391)]))
		self.assertEqual(sorted(list(self.m2ob.mtuples.keys())), sorted([('chr1', '*', 3391, 3400), ('chr1', '*', 3366, 3391)]))
		self.assertEqual(sorted(list(self.m2obac.mtuples.keys())), sorted([('chr1', '*', 3391, 3400), ('chr1', '*', 3366, 3400), ('chr1', '*', 3366, 3391)]))
		self.assertEqual(sorted(list(self.m3ob.mtuples.keys())), sorted([('chr1', '*', 3366, 3391, 3400)]))
		self.assertEqual(sorted(list(self.m3obac.mtuples.keys())), sorted([('chr1', '*', 3366, 3391, 3400)]))

	def test_correct_number_of_methylation_loci_in_fragment(self):
		self.assertEqual(self.nmlifot, 5)
		self.assertEqual(self.nmlifob, 3)

	def test_correct_methylation_type(self):
		self.assertEqual(self.m1ot.methylation_type, 'CG')
		self.assertEqual(self.m1ob.methylation_type, 'CG')
		self.assertEqual(self.m2cgchg.methylation_type, 'CG/CHG')

	def test_counts(self):
		self.assertEqual(self.m1ot.mtuples[('chr1', '*', 4562)], array.array('i', [1, 0]))

	def tearDown(self):
		os.remove(self.BAM.filename)

class TestExtractAndUpdateMethylationIndexFromPairedEndReads(unittest.TestCase):
	'''Test the function extract_and_update_methylation_index_from_single_end_read
	'''
	def setUp(self):

		def buildOTRead1():
			'''build an example read_1 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AATTTTAATTTTAATTTTTGCGGTATTTTTAGTCGGTTCGTTCGTTCGGGTTTGATTTGAG"
			read.flag = 99
			read.tid = 0
			read.pos = 450
			read.mapq = 255
			read.cigar = [(0,61)]
			read.rnext = 1
			read.pnext = 512
			read.tlen = 121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....")] + [("XR", "CT")]
			return read

		def buildOTRead2():
			'''build an example read_2 aligned to OT-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AGAATTGTGTTTCGTTTTTAGAGTATTATCGAAATTTGTGTAGAGGATAACGTAGCTTC"
			read.flag = 147
			read.tid = 0
			read.pos = 512
			read.mapq = 255
			read.cigar = [(0,59)]
			read.rnext = 1
			read.pnext = 450
			read.tlen = -121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "....x....h.xZ.hh..x......hh.xZ.....x....x......h..Z.x..H.xZ")] + [("XR", "GA")]
			return read

		def buildOBRead1():
			'''build an example read_1 aligned to OB-strand
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_22929891"
			read.seq = "AACGCAACTCCGCCCTCGCGATACTCTCCGAATCTATACTAAAAAAAACGCAACTCCGCCGAC"
			read.flag = 83
			read.tid = 0
			read.pos = 560
			read.mapq = 255
			read.cigar = [(0,63)]
			read.rnext = 1
			read.pnext = 492
			read.tlen = -131
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "GA")] + [("XM", "...Z..x....Z.....Z.Zx.h......Zxh...x.h..x.hh.h...Z.......Z..Zx.")] + [("XR", "CT")]
			return read

		def buildOBRead2():
			'''build an example read_2 aligned to OB-strand.
			'''

			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_22929891"
			read.seq = "CACCCGAATCTAACCTAAAAAAAACTATACTCCGCCTTCAAAATACCACCGAAATCTATACAAAAAA"
			read.flag = 163
			read.tid = 0
			read.pos = 492
			read.mapq = 255
			read.cigar = [(0,67)]
			read.rnext = 1
			read.pnext = 560
			read.tlen = 131
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "GA")] + [("XM", ".z...Zxh...x....x.hh.h....x.h....Z......x.h.......Z......x.h..x.hh.")] + [("XR", "GA")]
			return read

		def buildBAM():
			'''build a BAM file
			'''

			header = { 'HD': {'VN': '1.0'}, 'SQ': [{'LN': 10000, 'SN': 'chr1'}, {'LN': 20000, 'SN': 'chr2'}] }
			tempfile_path = tempfile.mkstemp()[1]
			BAM = pysam.Samfile(tempfile_path, "wb", header = header)
			return BAM

		# Create the reads, BAM file and methylation m-tuples
		self.otr_1 = buildOTRead1()
		self.otr_2 = buildOTRead2()
		self.obr_1 = buildOBRead1()
		self.obr_2 = buildOBRead2()
		self.BAM = buildBAM()
		self.BAM.write(self.otr_1)
		self.BAM.write(self.otr_2)
		self.BAM.write(self.obr_1)
		self.BAM.write(self.obr_2)
		self.filename = self.BAM.filename
		self.BAM.close()
		self.BAM = pysam.Samfile(self.filename, 'rb')
		self.FAILED_QC = open(tempfile.mkstemp()[1], 'w')
		self.m1ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m1otac, self.nmlifotac, self.nfsdtboca = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m2ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m2otac, self.nmlifotac, self.nfsdtboca = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m3ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m3otac, self.nmlifotac, self.nfsdtbosca = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m4ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 4, 'CG', {'chr1': 0}), m = 4, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m4otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 4, 'CG', {'chr1': 0}), m = 4, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m5ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 5, 'CG', {'chr1': 0}), m = 5, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m5otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 5, 'CG', {'chr1': 0}), m = 5, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m6ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 6, 'CG', {'chr1': 0}), m = 6, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m6otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 6, 'CG', {'chr1': 0}), m = 6, methylation_type = 'CG', all_combinations = True, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m7ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 7, 'CG', {'chr1': 0}), m = 7, methylation_type = 'CG', all_combinations = False, methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m7otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 7, 'CG', {'chr1': 0}), m = 7, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m8ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 8, 'CG', {'chr1': 0}), m = 8, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m8otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 8, 'CG', {'chr1': 0}), m = 8, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m9ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 9, 'CG', {'chr1': 0}), m = 9, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m9otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 9, 'CG', {'chr1': 0}), m = 9, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m10ot, self.nmlifot, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 10, 'CG', {'chr1': 0}), m = 10, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m10otac, self.nmlifotac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 10, 'CG', {'chr1': 0}), m = 10, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m1ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m1obac, self.nmlifobac, self.nfsdtbac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 1, 'CG', {'chr1': 0}), m = 1, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m2ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m2obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG', {'chr1': 0}), m = 2, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m3ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m3obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 3, 'CG', {'chr1': 0}), m = 3, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m4ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 4, 'CG', {'chr1': 0}), m = 4, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m4obac, self.nmlifobac, self.nfsdtbac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 4, 'CG', {'chr1': 0}), m = 4, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m5ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 5, 'CG', {'chr1': 0}), m = 5, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m5obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 5, 'CG', {'chr1': 0}), m = 5, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m6ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 6, 'CG', {'chr1': 0}), m = 6, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m6obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 6, 'CG', {'chr1': 0}), m = 6, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m7ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 7, 'CG', {'chr1': 0}), m = 7, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m7obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 7, 'CG', {'chr1': 0}), m = 7, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m8ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 8, 'CG', {'chr1': 0}), m = 8, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m8obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 8, 'CG', {'chr1': 0}), m = 8, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m9ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 9, 'CG', {'chr1': 0}), m = 9, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m9obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 9, 'CG', {'chr1': 0}), m = 9, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m10ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 10, 'CG', {'chr1': 0}), m = 10, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m10obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 10, 'CG', {'chr1': 0}), m = 10, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m11ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 11, 'CG', {'chr1': 0}), m = 11, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m11obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 11, 'CG', {'chr1': 0}), m = 11, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m12ob, self.nmlifob, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 12, 'CG', {'chr1': 0}), m = 12, all_combinations = False, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m12obac, self.nmlifobac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.obr_1, read_2 = self.obr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 12, 'CG', {'chr1': 0}), m = 12, all_combinations = True, methylation_type = 'CG', methylation_pattern = re.compile(r'[Zz]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m2cgchg, self.nmlifotcgchg, self.nfsdtbo = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG/CHG', {'chr1': 0}), m = 2, all_combinations = False, methylation_type = 'CG/CHG', methylation_pattern = re.compile(r'[ZzXx]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)
		self.m2cgchgac, self.nmlifotcgchgac, self.nfsdtboac = extract_and_update_methylation_index_from_paired_end_reads(read_1 = self.otr_1, read_2 = self.otr_2, BAM = self.BAM, methylation_m_tuples = MTuple('test', 2, 'CG/CHG', {'chr1': 0}), m = 2, all_combinations = True, methylation_type = 'CG/CHG', methylation_pattern = re.compile(r'[ZzXx]'), ignore_read_1_pos = [], ignore_read_2_pos = [], min_qual = 0, phred_offset = 33, ob_strand_offset = 1, overlap_check = 'Bismark', n_fragment_skipped_due_to_bad_overlap = 0, FAILED_QC = self.FAILED_QC)

	def test_correct_number_of_m_tuples(self):
		self.assertEqual(len(self.m1ot.mtuples), 10)
		self.assertEqual(len(self.m1otac.mtuples), 10)
		self.assertEqual(len(self.m2ot.mtuples), 9)
		self.assertEqual(len(self.m2otac.mtuples), 45)
		self.assertEqual(len(self.m3ot.mtuples), 8)
		self.assertEqual(len(self.m3otac.mtuples), 120)
		self.assertEqual(len(self.m4ot.mtuples), 7)
		self.assertEqual(len(self.m4otac.mtuples), 210)
		self.assertEqual(len(self.m5ot.mtuples), 6)
		self.assertEqual(len(self.m5otac.mtuples), 252)
		self.assertEqual(len(self.m6ot.mtuples), 5)
		self.assertEqual(len(self.m6otac.mtuples), 210)
		self.assertEqual(len(self.m7ot.mtuples), 4)
		self.assertEqual(len(self.m7otac.mtuples), 120)
		self.assertEqual(len(self.m8ot.mtuples), 3)
		self.assertEqual(len(self.m8otac.mtuples), 45)
		self.assertEqual(len(self.m9ot.mtuples), 2)
		self.assertEqual(len(self.m9otac.mtuples), 10)
		self.assertEqual(len(self.m10ot.mtuples), 1)
		self.assertEqual(len(self.m10otac.mtuples), 1)
		self.assertEqual(len(self.m1ob.mtuples), 12)
		self.assertEqual(len(self.m1obac.mtuples), 12)
		self.assertEqual(len(self.m2ob.mtuples), 11)
		self.assertEqual(len(self.m2obac.mtuples), 66)
		self.assertEqual(len(self.m3ob.mtuples), 10)
		self.assertEqual(len(self.m3obac.mtuples), 220)
		self.assertEqual(len(self.m4ob.mtuples), 9)
		self.assertEqual(len(self.m4obac.mtuples), 495)
		self.assertEqual(len(self.m5ob.mtuples), 8)
		self.assertEqual(len(self.m5obac.mtuples), 792)
		self.assertEqual(len(self.m6ob.mtuples), 7)
		self.assertEqual(len(self.m6obac.mtuples), 924)
		self.assertEqual(len(self.m7ob.mtuples), 6)
		self.assertEqual(len(self.m7obac.mtuples), 792)
		self.assertEqual(len(self.m8ob.mtuples), 5)
		self.assertEqual(len(self.m8obac.mtuples), 495)
		self.assertEqual(len(self.m9ob.mtuples), 4)
		self.assertEqual(len(self.m9obac.mtuples), 220)
		self.assertEqual(len(self.m10ob.mtuples), 3)
		self.assertEqual(len(self.m10obac.mtuples), 66)
		self.assertEqual(len(self.m11ob.mtuples), 2)
		self.assertEqual(len(self.m11obac.mtuples), 12)
		self.assertEqual(len(self.m12ob.mtuples), 1)
		self.assertEqual(len(self.m12obac.mtuples), 1)
		self.assertEqual(len(self.m2cgchg.mtuples), 24)
		self.assertEqual(len(self.m2cgchgac.mtuples), 300)

	def test_correct_m_tuple_ids(self):
		# Can't use assertItemsEqual because it is renamed assertCountEqual in Python 3.
		# Instead use assertEqual(sorted(expected), sorted(actual))
		# Only test a few values of m when --ac because of the large number of combinations this method produces.
		self.assertEqual(sorted(list(self.m1ot.mtuples.keys())), sorted([('chr1', '*', 563), ('chr1', '*', 571), ('chr1', '*', 525), ('chr1', '*', 493), ('chr1', '*', 469), ('chr1', '*', 484), ('chr1', '*', 489), ('chr1', '*', 497), ('chr1', '*', 471), ('chr1', '*', 542)]))
		self.assertEqual(sorted(list(self.m1otac.mtuples.keys())), sorted([('chr1', '*', 563), ('chr1', '*', 571), ('chr1', '*', 525), ('chr1', '*', 493), ('chr1', '*', 469), ('chr1', '*', 484), ('chr1', '*', 489), ('chr1', '*', 497), ('chr1', '*', 471), ('chr1', '*', 542)]))
		self.assertEqual(sorted(list(self.m2ot.mtuples.keys())), sorted([('chr1', '*', 497, 525), ('chr1', '*', 563, 571), ('chr1', '*', 484, 489), ('chr1', '*', 469, 471), ('chr1', '*', 542, 563), ('chr1', '*', 493, 497), ('chr1', '*', 471, 484), ('chr1', '*', 489, 493), ('chr1', '*', 525, 542)]))
		self.assertEqual(sorted(list(self.m2otac.mtuples.keys())), sorted([('chr1', '*', 469, 471), ('chr1', '*', 469, 484), ('chr1', '*', 469, 489), ('chr1', '*', 469, 493), ('chr1', '*', 469, 497), ('chr1', '*', 469, 525), ('chr1', '*', 469, 542), ('chr1', '*', 469, 563), ('chr1', '*', 469, 571), ('chr1', '*', 471, 484), ('chr1', '*', 471, 489), ('chr1', '*', 471, 493), ('chr1', '*', 471, 497), ('chr1', '*', 471, 525), ('chr1', '*', 471, 542), ('chr1', '*', 471, 563), ('chr1', '*', 471, 571), ('chr1', '*', 484, 489), ('chr1', '*', 484, 493), ('chr1', '*', 484, 497), ('chr1', '*', 484, 525), ('chr1', '*', 484, 542), ('chr1', '*', 484, 563), ('chr1', '*', 484, 571), ('chr1', '*', 489, 493), ('chr1', '*', 489, 497), ('chr1', '*', 489, 525), ('chr1', '*', 489, 542), ('chr1', '*', 489, 563), ('chr1', '*', 489, 571), ('chr1', '*', 493, 497), ('chr1', '*', 493, 525), ('chr1', '*', 493, 542), ('chr1', '*', 493, 563), ('chr1', '*', 493, 571), ('chr1', '*', 497, 525), ('chr1', '*', 497, 542), ('chr1', '*', 497, 563), ('chr1', '*', 497, 571), ('chr1', '*', 525, 542), ('chr1', '*', 525, 563), ('chr1', '*', 525, 571), ('chr1', '*', 542, 563), ('chr1', '*', 542, 571), ('chr1', '*', 563, 571)]))
		self.assertEqual(sorted(list(self.m3ot.mtuples.keys())), sorted([('chr1', '*', 493, 497, 525), ('chr1', '*', 497, 525, 542), ('chr1', '*', 489, 493, 497), ('chr1', '*', 525, 542, 563), ('chr1', '*', 471, 484, 489), ('chr1', '*', 484, 489, 493), ('chr1', '*', 542, 563, 571), ('chr1', '*', 469, 471, 484)]))
		self.assertEqual(sorted(list(self.m4ot.mtuples.keys())), sorted([('chr1', '*', 484, 489, 493, 497), ('chr1', '*', 525, 542, 563, 571), ('chr1', '*', 471, 484, 489, 493), ('chr1', '*', 493, 497, 525, 542), ('chr1', '*', 469, 471, 484, 489), ('chr1', '*', 497, 525, 542, 563), ('chr1', '*', 489, 493, 497, 525)]))
		self.assertEqual(sorted(list(self.m5ot.mtuples.keys())), sorted([('chr1', '*', 469, 471, 484, 489, 493), ('chr1', '*', 497, 525, 542, 563, 571), ('chr1', '*', 493, 497, 525, 542, 563), ('chr1', '*', 489, 493, 497, 525, 542), ('chr1', '*', 484, 489, 493, 497, 525), ('chr1', '*', 471, 484, 489, 493, 497)]))
		self.assertEqual(sorted(list(self.m6ot.mtuples.keys())), sorted([('chr1', '*', 469, 471, 484, 489, 493, 497), ('chr1', '*', 471, 484, 489, 493, 497, 525), ('chr1', '*', 489, 493, 497, 525, 542, 563), ('chr1', '*', 484, 489, 493, 497, 525, 542), ('chr1', '*', 493, 497, 525, 542, 563, 571)]))
		self.assertEqual(sorted(list(self.m7ot.mtuples.keys())), sorted([('chr1', '*', 469, 471, 484, 489, 493, 497, 525), ('chr1', '*', 471, 484, 489, 493, 497, 525, 542), ('chr1', '*', 484, 489, 493, 497, 525, 542, 563), ('chr1', '*', 489, 493, 497, 525, 542, 563, 571)]))
		self.assertEqual(sorted(list(self.m8ot.mtuples.keys())), sorted([('chr1', '*', 469, 471, 484, 489, 493, 497, 525, 542), ('chr1', '*', 484, 489, 493, 497, 525, 542, 563, 571), ('chr1', '*', 471, 484, 489, 493, 497, 525, 542, 563)]))
		self.assertEqual(sorted(list(self.m9ot.mtuples.keys())), sorted([('chr1', '*', 471, 484, 489, 493, 497, 525, 542, 563, 571), ('chr1', '*', 469, 471, 484, 489, 493, 497, 525, 542, 563)]))
		self.assertEqual(sorted(list(self.m10ot.mtuples.keys())), sorted([('chr1', '*', 469, 471, 484, 489, 493, 497, 525, 542, 563, 571)]))
		self.assertEqual(sorted(list(self.m10otac.mtuples.keys())), sorted([('chr1', '*', 469, 471, 484, 489, 493, 497, 525, 542, 563, 571)]))
		self.assertEqual(sorted(list(self.m1ob.mtuples.keys())), sorted([('chr1', '*', 563), ('chr1', '*', 617), ('chr1', '*', 493), ('chr1', '*', 577), ('chr1', '*', 525), ('chr1', '*', 542), ('chr1', '*', 579), ('chr1', '*', 589), ('chr1', '*', 571), ('chr1', '*', 620), ('chr1', '*', 497), ('chr1', '*', 609)]))
		self.assertEqual(sorted(list(self.m1obac.mtuples.keys())), sorted([('chr1', '*', 563), ('chr1', '*', 617), ('chr1', '*', 493), ('chr1', '*', 577), ('chr1', '*', 525), ('chr1', '*', 542), ('chr1', '*', 579), ('chr1', '*', 589), ('chr1', '*', 571), ('chr1', '*', 620), ('chr1', '*', 497), ('chr1', '*', 609)]))
		self.assertEqual(sorted(list(self.m2ob.mtuples.keys())), sorted([('chr1', '*', 589, 609), ('chr1', '*', 609, 617), ('chr1', '*', 571, 577), ('chr1', '*', 563, 571), ('chr1', '*', 577, 579), ('chr1', '*', 542, 563), ('chr1', '*', 493, 497), ('chr1', '*', 617, 620), ('chr1', '*', 579, 589), ('chr1', '*', 525, 542), ('chr1', '*', 497, 525)]))
		self.assertEqual(sorted(list(self.m2obac.mtuples.keys())), sorted([('chr1', '*', 493, 497), ('chr1', '*', 493, 525), ('chr1', '*', 493, 542), ('chr1', '*', 493, 563), ('chr1', '*', 493, 571), ('chr1', '*', 493, 577), ('chr1', '*', 493, 579), ('chr1', '*', 493, 589), ('chr1', '*', 493, 609), ('chr1', '*', 493, 617), ('chr1', '*', 493, 620), ('chr1', '*', 497, 525), ('chr1', '*', 497, 542), ('chr1', '*', 497, 563), ('chr1', '*', 497, 571), ('chr1', '*', 497, 577), ('chr1', '*', 497, 579), ('chr1', '*', 497, 589), ('chr1', '*', 497, 609), ('chr1', '*', 497, 617), ('chr1', '*', 497, 620), ('chr1', '*', 525, 542), ('chr1', '*', 525, 563), ('chr1', '*', 525, 571), ('chr1', '*', 525, 577), ('chr1', '*', 525, 579), ('chr1', '*', 525, 589), ('chr1', '*', 525, 609), ('chr1', '*', 525, 617), ('chr1', '*', 525, 620), ('chr1', '*', 542, 563), ('chr1', '*', 542, 571), ('chr1', '*', 542, 577), ('chr1', '*', 542, 579), ('chr1', '*', 542, 589), ('chr1', '*', 542, 609), ('chr1', '*', 542, 617), ('chr1', '*', 542, 620), ('chr1', '*', 563, 571), ('chr1', '*', 563, 577), ('chr1', '*', 563, 579), ('chr1', '*', 563, 589), ('chr1', '*', 563, 609), ('chr1', '*', 563, 617), ('chr1', '*', 563, 620), ('chr1', '*', 571, 577), ('chr1', '*', 571, 579), ('chr1', '*', 571, 589), ('chr1', '*', 571, 609), ('chr1', '*', 571, 617), ('chr1', '*', 571, 620), ('chr1', '*', 577, 579), ('chr1', '*', 577, 589), ('chr1', '*', 577, 609), ('chr1', '*', 577, 617), ('chr1', '*', 577, 620), ('chr1', '*', 579, 589), ('chr1', '*', 579, 609), ('chr1', '*', 579, 617), ('chr1', '*', 579, 620), ('chr1', '*', 589, 609), ('chr1', '*', 589, 617), ('chr1', '*', 589, 620), ('chr1', '*', 609, 617), ('chr1', '*', 609, 620), ('chr1', '*', 617, 620)]))
		self.assertEqual(sorted(list(self.m3ob.mtuples.keys())), sorted([('chr1', '*', 571, 577, 579), ('chr1', '*', 493, 497, 525), ('chr1', '*', 609, 617, 620), ('chr1', '*', 497, 525, 542), ('chr1', '*', 589, 609, 617), ('chr1', '*', 579, 589, 609), ('chr1', '*', 525, 542, 563), ('chr1', '*', 563, 571, 577), ('chr1', '*', 542, 563, 571), ('chr1', '*', 577, 579, 589)]))
		self.assertEqual(sorted(list(self.m4ob.mtuples.keys())), sorted([('chr1', '*', 577, 579, 589, 609), ('chr1', '*', 571, 577, 579, 589), ('chr1', '*', 563, 571, 577, 579), ('chr1', '*', 525, 542, 563, 571), ('chr1', '*', 542, 563, 571, 577), ('chr1', '*', 579, 589, 609, 617), ('chr1', '*', 493, 497, 525, 542), ('chr1', '*', 497, 525, 542, 563), ('chr1', '*', 589, 609, 617, 620)]))
		self.assertEqual(sorted(list(self.m5ob.mtuples.keys())), sorted([('chr1', '*', 563, 571, 577, 579, 589), ('chr1', '*', 571, 577, 579, 589, 609), ('chr1', '*', 577, 579, 589, 609, 617), ('chr1', '*', 497, 525, 542, 563, 571), ('chr1', '*', 493, 497, 525, 542, 563), ('chr1', '*', 579, 589, 609, 617, 620), ('chr1', '*', 542, 563, 571, 577, 579), ('chr1', '*', 525, 542, 563, 571, 577)]))
		self.assertEqual(sorted(list(self.m6ob.mtuples.keys())), sorted([('chr1', '*', 577, 579, 589, 609, 617, 620), ('chr1', '*', 497, 525, 542, 563, 571, 577), ('chr1', '*', 571, 577, 579, 589, 609, 617), ('chr1', '*', 493, 497, 525, 542, 563, 571), ('chr1', '*', 563, 571, 577, 579, 589, 609), ('chr1', '*', 525, 542, 563, 571, 577, 579), ('chr1', '*', 542, 563, 571, 577, 579, 589)]))
		self.assertEqual(sorted(list(self.m7ob.mtuples.keys())), sorted([('chr1', '*', 525, 542, 563, 571, 577, 579, 589), ('chr1', '*', 493, 497, 525, 542, 563, 571, 577), ('chr1', '*', 497, 525, 542, 563, 571, 577, 579), ('chr1', '*', 542, 563, 571, 577, 579, 589, 609), ('chr1', '*', 571, 577, 579, 589, 609, 617, 620), ('chr1', '*', 563, 571, 577, 579, 589, 609, 617)]))
		self.assertEqual(sorted(list(self.m8ob.mtuples.keys())), sorted([('chr1', '*', 493, 497, 525, 542, 563, 571, 577, 579), ('chr1', '*', 497, 525, 542, 563, 571, 577, 579, 589), ('chr1', '*', 563, 571, 577, 579, 589, 609, 617, 620), ('chr1', '*', 525, 542, 563, 571, 577, 579, 589, 609), ('chr1', '*', 542, 563, 571, 577, 579, 589, 609, 617)]))
		self.assertEqual(sorted(list(self.m9ob.mtuples.keys())), sorted([('chr1', '*', 497, 525, 542, 563, 571, 577, 579, 589, 609), ('chr1', '*', 493, 497, 525, 542, 563, 571, 577, 579, 589), ('chr1', '*', 542, 563, 571, 577, 579, 589, 609, 617, 620), ('chr1', '*', 525, 542, 563, 571, 577, 579, 589, 609, 617)]))
		self.assertEqual(sorted(list(self.m10ob.mtuples.keys())), sorted([('chr1', '*', 497, 525, 542, 563, 571, 577, 579, 589, 609, 617), ('chr1', '*', 493, 497, 525, 542, 563, 571, 577, 579, 589, 609), ('chr1', '*', 525, 542, 563, 571, 577, 579, 589, 609, 617, 620)]))
		self.assertEqual(sorted(list(self.m11ob.mtuples.keys())), sorted([('chr1', '*', 497, 525, 542, 563, 571, 577, 579, 589, 609, 617, 620), ('chr1', '*', 493, 497, 525, 542, 563, 571, 577, 579, 589, 609, 617)]))
		self.assertEqual(sorted(list(self.m12ob.mtuples.keys())), sorted([('chr1', '*', 493, 497, 525, 542, 563, 571, 577, 579, 589, 609, 617, 620)]))
		self.assertEqual(sorted(list(self.m12obac.mtuples.keys())), sorted([('chr1', '*', 493, 497, 525, 542, 563, 571, 577, 579, 589, 609, 617, 620)]))

	def test_correct_number_of_methylation_loci_in_fragment(self):
		self.assertEqual(self.nmlifot, 10)
		self.assertEqual(self.nmlifob, 12)

	def test_correct_methylation_type(self):
		self.assertEqual(self.m1ot.methylation_type, 'CG')
		self.assertEqual(self.m1ob.methylation_type, 'CG')
		self.assertEqual(self.m2cgchg.methylation_type, 'CG/CHG')

	def test_counts(self):
		self.assertEqual(self.m1ot.mtuples[('chr1', '*', 563)], array.array('i', [1, 0]))

	def tearDown(self):
		os.remove(self.BAM.filename)
		os.remove(self.FAILED_QC.name)

class TestMTuple(unittest.TestCase):
	'''Test the class MTuple and its methods
	'''

	def setUp(self):

		def buildOTRead():
			'''build an example read aligned to OT-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "@SALK_2077_FC6295TAAXX:2:107:9396:15019#0/1"
			read.seq = "GGGGAAGGTGTTATGGAGTTTTTTACGATTTTTAGTCGTTTTCGTTTTTTTTTGTTTGTGGTTGTTGCGGTGGCGGTAGAGGAGGG"
			read.flag = 0
			read.tid = 0
			read.pos = 4536
			read.mapq = 255
			read.cigar = [(0,86)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "DBDB2;@>)@@F?EFG@GBGGGGDDBG@DGGGGEEFHHEGHHHHEFHHHHFHHHFHHHGHGBCEAA@?@?/A@>@3,.6,AA,@>="
			read.tags = read.tags + [("XG", "CT")] + [("XM", "...........h......hhhhh..Z....hhx...Z..hh.Z..hh.hh.x..hx.....x..x..Z.....Z..x.........")] + [("XR", "CT")]
			return read

		def buildOBRead():
			'''build an example read aligned to OB-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "@ECKER_1116_FC623CNAAXX:2:21:18515:1127#0/1"
			read.seq = "CTTCCTAACAAACAACTACACCACTACCTAACGCTATACCCTTCCTTTACTCTACCCACTAAAAACAATATTTATCATAAACCT"
			read.flag = 16
			read.tid = 0
			read.pos = 3334
			read.mapq = 255
			read.cigar = [(0,84)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "G7@G@BGB@GGGGGDIEEBIBA<AHEGEEEGGGDDEDFFEIIHIIGGDGGGGGGGGGGDGDBED<FAAFEGGGGGIHIFIGBDG"
			read.tags = read.tags + [("XG", "GA")] + [("XM", "......x...xh..x..x.......x...xh.Z..x.h..........h....x...z..xh.h..zx.h...h....hhh...")] + [("XR", "CT")]
			return read

		def buildOTRead1():
			'''build an example read_1 aligned to OT-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AATTTTAATTTTAATTTTTGCGGTATTTTTAGTCGGTTCGTTCGTTCGGGTTTGATTTGAG"
			read.flag = 99
			read.tid = 0
			read.pos = 450
			read.mapq = 255
			read.cigar = [(0,61)]
			read.rnext = 1
			read.pnext = 512
			read.tlen = 121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....")] + [("XR", "CT")]
			return read

		def buildOTRead2():
			'''build an example read_2 aligned to OT-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_8"
			read.seq = "AGAATTGTGTTTCGTTTTTAGAGTATTATCGAAATTTGTGTAGAGGATAACGTAGCTTC"
			read.flag = 147
			read.tid = 0
			read.pos = 512
			read.mapq = 255
			read.cigar = [(0,59)]
			read.rnext = 1
			read.pnext = 450
			read.tlen = -121
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "CT")] + [("XM", "....x....h.xZ.hh..x......hh.xZ.....x....x......h..Z.x..H.xZ")] + [("XR", "GA")]
			return read

		def buildOBRead1():
			'''build an example read_1 aligned to OB-strand
			'''
			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_22929891"
			read.seq = "AACGCAACTCCGCCCTCGCGATACTCTCCGAATCTATACTAAAAAAAACGCAACTCCGCCGAC"
			read.flag = 83
			read.tid = 0
			read.pos = 560
			read.mapq = 255
			read.cigar = [(0,63)]
			read.rnext = 1
			read.pnext = 492
			read.tlen = -131
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "GA")] + [("XM", "...Z..x....Z.....Z.Zx.h......Zxh...x.h..x.hh.h...Z.......Z..Zx.")] + [("XR", "CT")]
			return read

		def buildOBRead2():
			'''build an example read_2 aligned to OB-strand.
			'''
			read = pysam.AlignedRead()
			read.qname = "ADS-adipose_chr1_22929891"
			read.seq = "CACCCGAATCTAACCTAAAAAAAACTATACTCCGCCTTCAAAATACCACCGAAATCTATACAAAAAA"
			read.flag = 163
			read.tid = 0
			read.pos = 492
			read.mapq = 255
			read.cigar = [(0,67)]
			read.rnext = 1
			read.pnext = 560
			read.tlen = 131
			read.qual = "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
			read.tags = read.tags + [("XG", "GA")] + [("XM", ".z...Zxh...x....x.hh.h....x.h....Z......x.h.......Z......x.h..x.hh.")] + [("XR", "GA")]
			return read

		def buildBAM():
			'''build a BAM file
			'''
			header = { 'HD': {'VN': '1.0'}, 'SQ': [{'LN': 10000, 'SN': 'chr1'}, {'LN': 20000, 'SN': 'chr2'}] }
			tempfile_path = tempfile.mkstemp()[1]
			BAM = pysam.Samfile(tempfile_path, "wb", header = header)
			return BAM

		# Create the reads, BAM file and methylation m-tuples
		# Single-end
		self.otr = buildOTRead()
		self.obr = buildOBRead()
		self.BAM = buildBAM()
		self.BAM.write(self.otr)
		self.BAM.write(self.obr)
		self.filename = self.BAM.filename
		self.BAM.close()
		self.BAM = pysam.Samfile(self.filename, 'rb')
		self.wfotr = MTuple('test', 2, 'CG', {'chr1': 0})
		self.wfotr.increment_count(('chr1', 4562, 4573), 'ZZ', self.otr, None)
		self.wfobr = MTuple('test', 2, 'CG', {'chr1': 0})
		self.wfobr.increment_count(('chr1', 3366, 3391), 'ZZ', self.otr, None)
		self.wfotrcgchg = MTuple('test', 3, 'CG/CHG', {'chr1': 0})
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'ZXZ', self.otr, None)

		# Paired-end
		self.otr_1 = buildOTRead1()
		self.otr_2 = buildOTRead2()
		self.obr_1 = buildOBRead1()
		self.obr_2 = buildOBRead2()
		self.BAMPE = buildBAM()
		self.BAMPE.write(self.otr_1)
		self.BAMPE.write(self.otr_2)
		self.BAMPE.write(self.obr_1)
		self.BAMPE.write(self.obr_2)
		self.filename = self.BAMPE.filename
		self.BAMPE.close()
		self.BAMPE = pysam.Samfile(self.filename, 'rb')
		self.wfotrpe = MTuple('test', 2, 'CG', {'chr1': 0})
		self.wfotrpe.increment_count(('chr1', 497, 525), 'ZZ', self.otr_1, self.otr_2)
		self.wfobrpe = MTuple('test', 2, 'CG', {'chr1': 0})
		self.wfobrpe.increment_count(('chr1', 563, 571), 'ZZ', self.obr_1, self.obr_2)
		self.wfotrpecgchg = MTuple('test', 3, 'CG/CHG', {'chr1': 0})
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'ZZX', self.otr_1, self.otr_2)

	def test_init_se(self):
		self.assertEqual(self.wfotr.chr_map, {'chr1': 0})
		self.assertEqual(self.wfotr.comethylation_patterns, ['MM', 'MU', 'UM', 'UU'])
		self.assertEqual(self.wfotr.m, 2)
		self.assertEqual(list(self.wfotr.mtuples.keys()), [('chr1', 4562, 4573)])
		self.assertEqual(list(self.wfotr.mtuples.values()), [array.array('i', [1, 0, 0, 0])])
		self.assertEqual(self.wfotr.methylation_type, 'CG')
		self.assertEqual(self.wfobr.methylation_type, 'CG')
		self.assertEqual(self.wfotrcgchg.methylation_type, 'CG/CHG')

	def test_init_pe(self):
		self.assertEqual(self.wfotrpe.methylation_type, 'CG')
		self.assertEqual(self.wfobrpe.methylation_type, 'CG')
		self.assertEqual(self.wfotrpecgchg.methylation_type, 'CG/CHG')

	def test_increment_count_ot_se(self):
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [1, 0, 0, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'MM', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 0, 0, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'MU', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 1, 0, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'UM', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 1, 1, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'UU', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 1, 1, 1]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'MM', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [3, 1, 1, 1]))

	def test_increment_count_ob_se(self):
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [1, 0, 0, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'MM', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 0, 0, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'MU', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 1, 0, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'UM', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 1, 1, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'UU', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 1, 1, 1]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'MM', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [3, 1, 1, 1]))

	def test_increment_count_ctot_se(self):
		self.otr.tags = []
		self.otr.tags = self.otr.tags + [("XG", "CT")] + [("XM", "...........h......hhhhh..Z....hhx...Z..hh.Z..hh.hh.x..hx.....x..x..Z.....Z..x.........")] + [("XR", "GA")]
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [1, 0, 0, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'MM', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 0, 0, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'MU', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 1, 0, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'UM', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 1, 1, 0]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'UU', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [2, 1, 1, 1]))
		self.wfotr.increment_count(('chr1', 4562, 4573), 'MM', self.otr, None)
		self.assertEqual(self.wfotr.mtuples[('chr1', 4562, 4573)], array.array('i', [3, 1, 1, 1]))

	def test_increment_count_ctob_se(self):
		self.obr.tags = []
		self.obr.tags = self.obr.tags + [("XG", "GA")] + [("XM", "......x...xh..x..x.......x...xh.Z..x.h..........h....x...z..xh.h..zx.h...h....hhh...")] + [("XR", "GA")]
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [1, 0, 0, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'MM', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 0, 0, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'MU', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 1, 0, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'UM', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 1, 1, 0]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'UU', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [2, 1, 1, 1]))
		self.wfobr.increment_count(('chr1', 3366, 3391), 'MM', self.obr, None)
		self.assertEqual(self.wfobr.mtuples[('chr1', 3366, 3391)], array.array('i', [3, 1, 1, 1]))

	def test_increment_count_multiple_methylation_types_se(self):
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [1, 0, 0, 0, 0, 0, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'MMM', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 0, 0, 0, 0, 0, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'MMU', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 0, 0, 0, 0, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'MUM', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 1, 0, 0, 0, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'MUU', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 1, 1, 0, 0, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'UMM', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 1, 1, 1, 0, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'UMU', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 1, 1, 1, 1, 0, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'UUM', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 1, 1, 1, 1, 1, 0]))
		self.wfotrcgchg.increment_count(('chr1', 4562, 4569, 4573), 'UUU', self.otr, None)
		self.assertEqual(self.wfotrcgchg.mtuples[('chr1', 4562, 4569, 4573)], array.array('i', [2, 1, 1, 1, 1, 1, 1, 1]))

	def test_increment_count_ot_pe(self):
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [1, 0, 0, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'MM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 0, 0, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'MU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 1, 0, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'UM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 1, 1, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'UU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 1, 1, 1]))

	def test_increment_count_ob_pe(self):
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [1, 0, 0, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'MM', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 0, 0, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'MU', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 1, 0, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'UM', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 1, 1, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'UU', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 1, 1, 1]))

	def test_increment_count_ctot_pe(self):
		self.otr_1.tags = []
		self.otr_1.tags = self.otr_1.tags + [('XG', 'CT'), ('XM', '..hhh...hhh...hhh.z.Z....hhh.x..xZ..hxZ.hxZ.hxZ....x...hx....'), ('XR', 'GA')]
		self.otr_2.tags = []
		self.otr_2.tags = self.otr_2.tags + [('XG', 'CT'), ('XM', '....x....h.xZ.hh..x......hh.xZ.....x....x......h..Z.x..H.xZ'), ('XR', 'CT')]
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [1, 0, 0, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'MM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 0, 0, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'MU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 1, 0, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'UM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 1, 1, 0]))
		self.wfotrpe.increment_count(('chr1', 497, 525), 'UU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpe.mtuples[('chr1', 497, 525)], array.array('i', [2, 1, 1, 1]))

	def test_increment_count_ctob_pe(self):
		self.obr_1.tags = []
		self.obr_1.tags = self.obr_1.tags + [('XG', 'GA'), ('XM', '...Z..x....Z.....Z.Zx.h......Zxh...x.h..x.hh.h...Z.......Z..Zx.'), ('XR', 'GA')]
		self.obr_2.tags = []
		self.obr_2.tags = self.obr_2.tags + [('XG', 'GA'), ('XM', '.z...Zxh...x....x.hh.h....x.h....Z......x.h.......Z......x.h..x.hh.'), ('XR', 'CT')]
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [1, 0, 0, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'MM', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 0, 0, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'MU', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 1, 0, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'UM', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 1, 1, 0]))
		self.wfobrpe.increment_count(('chr1', 563, 571), 'UU', self.obr_1, self.obr_2)
		self.assertEqual(self.wfobrpe.mtuples[('chr1', 563, 571)], array.array('i', [2, 1, 1, 1]))

	def test_increment_count_multiple_methylation_types_pe(self):
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [1, 0, 0, 0, 0, 0, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'MMM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 0, 0, 0, 0, 0, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'MMU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 0, 0, 0, 0, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'MUM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 1, 0, 0, 0, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'MUU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 1, 1, 0, 0, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'UMM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 1, 1, 1, 0, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'UMU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 1, 1, 1, 1, 0, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'UUM', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 1, 1, 1, 1, 1, 0]))
		self.wfotrpecgchg.increment_count(('chr1', 497, 525, 534), 'UUU', self.otr_1, self.otr_2)
		self.assertEqual(self.wfotrpecgchg.mtuples[('chr1', 497, 525, 534)], array.array('i', [2, 1, 1, 1, 1, 1, 1, 1]))

	def test_invalid_comethylation_pattern(self):
		with self.assertRaises(SystemExit) as cm:
			self.wfotr.increment_count(('chr1', 4562, 4573), 'MMM', self.otr, None)
			self.assertEqual(cm.exception.code, 1)
		with self.assertRaises(SystemExit) as cm:
			self.wfotr.increment_count(('chr1', 4562, 4573), 'M', self.otr, None)
			self.assertEqual(cm.exception.code, 1)
		with self.assertRaises(SystemExit) as cm:
			self.wfotr.increment_count(('chr1', 4562, 4573), 'MA', self.otr, None)
			self.assertEqual(cm.exception.code, 1)
		with self.assertRaises(SystemExit) as cm:
			self.wfotr.increment_count(('chr1', 4562, 4573), 'mm', self.otr, None)
			self.assertEqual(cm.exception.code, 1)

	def test_invalid_m(self):
		self.assertRaises(ValueError, MTuple, 'test', -2, 'CG', {'chr1': 0})
		self.assertRaises(ValueError, MTuple, 'test', 2.3, 'CG', {'chr1': 0})
		self.assertRaises(ValueError, MTuple, 'test', 2.0, 'CG', {'chr1': 0})

	def test_invalid_methylation_type(self):
		self.assertRaises(ValueError, MTuple, 'test', -2, 'CT', {'chr1': 0})
		self.assertRaises(ValueError, MTuple, 'test', -2, 'CG-CHG', {'chr1': 0})
		self.assertRaises(ValueError, MTuple, 'test', -2, 'CHG/CHG', {'chr1': 0})
		self.assertRaises(ValueError, MTuple, 'test', -2, 'CHG/CG', {'chr1': 0})

	def tearDown(self):
		os.remove(self.BAM.filename)
		os.remove(self.BAMPE.filename)

class TestGetStrand(unittest.TestCase):

	def setUp(self):
		def buildOTSE():
			read = pysam.AlignedRead()
			read.qname = "SRR020138.15030048_SALK_2029:7:100:1740:1801_length=86"
			read.seq = "CGAATGTTTTTTATTATGAATGAGAGTTTGTTAAATTAGTTGGTTTTAGG"
			read.flag = 0
			read.tid = 0
			read.pos = 245746845
			read.mapq = 255
			read.cigar = [(0, 50)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "BC?BBBBBCCCCAA@BCB?AB@AB>CABB@@BB@?BB497@@B:@@B5>@"
			read.tags = read.tags + [("XM", "Z........h....h.............z.......x..x.....h....")] + [('XR', 'CT')] + [('XG', 'CT')]
			return read

		def buildOBSE():
			read = pysam.AlignedRead()
			read.qname = "SRR020138.15033460_SALK_2029:7:100:1783:2004_length=86"
			read.seq = "GTATACGCTAATTTTATAACCTAAAAATTTACTAAATTCATTAATCAAAT"
			read.flag = 16
			read.tid = 0
			read.pos = 96804459
			read.mapq = 255
			read.cigar = [(0, 50)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "CCBCACCBBCCCAACBBCAB@CCCCCCBBCCCCCCCCCBBBBCBCACBCB"
			read.tags = read.tags + [('XM', "Z.h...Z..x.....h.......hh.h......x........h....x..")] + [('XR', 'CT')] + [('XG', 'GA')]
			return read

		def buildCTOTSE():
			read = pysam.AlignedRead()
			read.qname = "SRR020138.15026483_SALK_2029:7:100:1698:1069_length=86"
			read.seq = "CCTCCATCATCATTCCTAATTTCTCCTTCCTCCCTTTCTACTTCCTCCTT"
			read.flag = 0
			read.tid = 0
			read.pos = 69393512
			read.mapq = 255
			read.cigar = [(0, 50)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "1)9<)@96'3%6@5:0=3::;;:89*;:@AA@=;A=3)2)1@>*9;-4:A"
			read.tags = read.tags + [('XM', 'H.h...h...H...HHh.................................')] + [('XR', 'GA')] + [('XG', 'CT')]
			return read

		def buildCTOBSE():
			read = pysam.AlignedRead()
			read.qname = "SRR020138.15034119_SALK_2029:7:100:1792:1889_length=86"
			read.seq = "ATGGAATGGAAAGGAAGGGAATTTAATGGAATGGAATGGAATGGAATGGA"
			read.flag = 16
			read.tid = 0
			read.pos = 10784296
			read.mapq = 255
			read.cigar = [(0, 50)]
			read.rnext = 0
			read.pnext = 0
			read.tlen = 0
			read.qual = "BCBBBBCCBCAA=@?B?A?@@BCCBCCAAA=B9@B?A=9?BBB??AC@2="
			read.tags = read.tags + [('XM', '..HH...HHhh.HH...HH........HH.h.H..h.H..h.HH.h.HH.')] + [('XR', 'GA')] + [('XG', 'GA')]
			return read

		def buildOTPE():
			read_1 = pysam.AlignedRead()
			read_1.qname = "SRR400564.1684335_HAL:1133:C010EABXX:8:1108:18844:132483_length=101"
			read_1.seq = "CGAGTTCGTTTAAAGAGTAATTAGTTATTTTTGTAAGGTTTGGTTAGGGTTATAGAAGGTTTTTTTGGATGGTAATTTTGGTTGCGTTTTGTATTTGAATA"
			read_1.flag = 99
			read_1.tid = 0
			read_1.pos = 19978967
			read_1.mapq = 255
			read_1.cigar = [(0, 101)]
			read_1.rnext = 0
			read_1.pnext = 19979235
			read_1.tlen = 369
			read_1.qual = "BC@FDFFFHHHHHJIHICHHHIIJJIGGJJJJJHGIF11?CGHIJIIJJHHHIIJIHHG9BFHIJFFDAC@?6;;-;AC@?DD<98@BDBDD>CDD#####"
			read_1.tags = read_1.tags + [('XM', 'Z...h.Z.h.h......h..hx..hh.hh.x..h.....x...hx....h..x......hhhhhx...........hx...x..Z...x..h.hx....h.')] + [('XR', 'CT')] + [('XG', 'CT')]
			read_2 = pysam.AlignedRead()
			read_2.qname = "SRR400564.1684335_HAL:1133:C010EABXX:8:1108:18844:132483_length=101"
			read_2.seq = "TATTGAGTTGTGTGTATGTCAGGTAAAGTTAGGTTGGTTTAAAGAGTAATTAGTTATTTTTGTAAGGTTGGGTTAGGAGAAGGCGGATTAGTTATTAATTT"
			read_2.flag = 147
			read_2.tid = 0
			read_2.pos = 19979235
			read_2.mapq = 255
			read_2.cigar = [(0, 101)]
			read_2.rnext = 0
			read_2.pnext = 19978967
			read_2.tlen = -369
			read_2.qual = "EDDDDDDBBDDDDDDDCDEEEEEFFFFFHHGHIIFJJJIJJJJIJJJJJIHIJJIJJJJJIJJJJJJJJJJJJJJJJJJJJJJJJJJJHHHHHFFFFFCCC"
			read_2.tags = read_2.tags + [('XM', 'h.x....x......h.z.hX...h....hx...x...h.h......h..hx..hh.hh.x..h....x....hx.........Z...hx..hh.hh..hh.')] + [('XR', 'GA')] + [('XG', 'CT')]
			return read_1, read_2

		def buildOBPE():
			read_1 = pysam.AlignedRead()
			read_1.qname = "SRR400564.241291_HAL:1133:C010EABXX:8:1102:8553:52618_length=101"
			read_1.seq = "GATCACCTAAATCGAAAATTAAAAACCAACCTAACCAACACGATAAAACCCCATCTCTACTAAAATACAAAAACTAACCAAACGTAATAACAAACACCTAT"
			read_1.flag = 83
			read_1.tid = 0
			read_1.pos = 19195980
			read_1.mapq = 255
			read_1.cigar = [(0, 101)]
			read_1.rnext = 0
			read_1.pnext = 19195917
			read_1.tlen = -164
			read_1.qual = "#####@:4B@;(85DDD@:;DDBBAACD?FD@HHHFIIJIIIHFJIFDJJIIFBGFGIGIGJIHFFDEJJJGIIGJIJJJJIJJHJIHHHHHHFDDDF@@@"
			read_1.tags = read_1.tags + [('XM', 'Z.......xhh..Zxh.h..h..h....x...xh.......Zx.h...............................h...xh.Z.hh.hh..x......x.')] + [('XR', 'CT')] + [('XG', 'GA')]
			read_2 = pysam.AlignedRead()
			read_2.qname = "SRR400564.241291_HAL:1133:C010EABXX:8:1102:8553:52618_length=101"
			read_2.seq = "TATAAAACAAAACATAATAACTCATACCTATAATCCCAACACTTTAAAAATCTAAAACAAACCGATCACCTAAATCGAAAATTAAAAACCAACCTAACCAA"
			read_2.flag = 163
			read_2.tid = 0
			read_2.pos = 19195917
			read_2.mapq = 255
			read_2.cigar = [(0, 101)]
			read_2.rnext = 0
			read_2.pnext = 19195980
			read_2.tlen = 164
			read_2.qual = "CCCFFFFFHHHHHJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJEHHIJJJJJJIJJIIJHHHFFFFFEEDEEDDDDDDDDDDDDDDDDDDDDDD"
			read_2.tags = read_2.tags + [("XM", ".x...hh..xh..z.hh.hh.....h...x........x......hhh.h...x.hh...h..Z.......xhh..Zxh.h..h..h....x...xh....")] + [('XR', 'GA')] + [('XG', 'GA')]
			return read_1, read_2

		def buildCTOTPE():
			read_1 = pysam.AlignedRead()
			read_1.qname = "SRR400564.6667900_HAL:1133:C010EABXX:8:2207:16412:102567_length=101"
			read_1.seq = "CGACCCCCCATCTATTCATCCATCCACCCCCCCCCCCACCCATCCATTAATTTATTCATCCATCCACCCACCCATCCACCATCCATTCAACCATCCATCCA"
			read_1.flag = 99
			read_1.tid = 0
			read_1.pos = 3287553
			read_1.mapq = 255
			read_1.cigar = [(0, 101)]
			read_1.rnext = 0
			read_1.pnext = 3287383
			read_1.tlen = -271
			read_1.qual = "#########################################73GE@CEGECGDFAFAB@IGD?FB0HF?1JHGF@HFAJIHFJJIHGEA22222224B@:4"
			read_1.tags = read_1.tags + [('XM', 'Z...HH.HH..H....H..HH..HH..HH.HHH.HHH..HH..HH...........H..HH..HH.HHH.HHH..HH.HH..HH...H..HH..HH..HH.')] + [('XR', 'GA')] + [('XG', 'CT')]
			read_2 = pysam.AlignedRead()
			read_2.qname = "SRR400564.6667900_HAL:1133:C010EABXX:8:2207:16412:102567_length=101"
			read_2.seq = "ATCCACCATCTATTCATCCATCCGTCCACCCACCCATCCATCCATTAATTATCCATCCACCCACCCATCCACCATCCATTCATCCATCCATCCATCCATAC"
			read_2.flag = 147
			read_2.tid = 0
			read_2.pos = 3287383
			read_2.mapq = 255
			read_2.cigar = [(0, 101)]
			read_2.rnext = 0
			read_2.pnext = 3287553
			read_2.tlen = 271
			read_2.qual = "CCCFFFFFHHHHHJJJJJJJJJJIIJIGHIJIJJJJJJJJJJJJJJJJJJGGCBFHCHGGCHIIJHHHFFFFECEDEDDDDE@>@CD:ACCDDD>>?::@C"
			read_2.tags = read_2.tags + [('XM', '..HH.HH..H....H..HH..XZ..HH.HHH.HHH..HH..HH.........HH..HH.HHH.HHH..HH.HH..HH...H..HH..HH..HH..HH...H')] + [('XR', 'CT')] + [('XG', 'CT')]
			return read_1, read_2

		def buildCTOBPE():
			read_1 = pysam.AlignedRead()
			read_1.qname = "SRR400564.4547217_HAL:1133:C010EABXX:8:2105:21225:192741_length=101"
			read_1.seq = "AAGGAAGGAGGGAAGGAAGGAAATAAAGAAAGGAAAAAAGGAAAGAAAGAAAAATAAAGAAATAAAGGAAGGAGGGAAGGAAGGAAAGAATGAAAGAAAGA"
			read_1.flag = 83
			read_1.tid = 0
			read_1.pos = 55291120
			read_1.mapq = 255
			read_1.cigar = [(0, 101)]
			read_1.rnext = 0
			read_1.pnext = 55291173
			read_1.tlen = 154
			read_1.qual = "1:BD42222300<CGHIIIJIIJJIIJGIIIIIIIJJIIJIJIIIIIGHIIIIHHGGGFFFFFFDECCDCBBDB@BBA<?BC<0<AC?CB@:@CC@CBC:>"
			read_1.tags = read_1.tags + [('XM', 'z..Hh.HHh..Hh..Hh...h...h...h...H.h..hh..h...h..Hh...h...h.....hh......Hh...h...h..........H..hH.hhH.')] + [('XR', 'GA')] + [('XG', 'GA')]
			read_2 = pysam.AlignedRead()
			read_2.qname = "SRR400564.4547217_HAL:1133:C010EABXX:8:2105:21225:192741_length=101"
			read_2.seq = "AAAAGAAAAAGGAAAAAAGGAAAGAAAGAAAAATAAATGAAGGAGGGAAGGAAGGAAAGAAAGAAGGGAAGAAAGAAAAGTAAATGAAGGAGGGAAAGAAG"
			read_2.flag = 163
			read_2.tid = 0
			read_2.pos = 55291173
			read_2.mapq = 255
			read_2.cigar = [(0, 101)]
			read_2.rnext = 0
			read_2.pnext = 55291120
			read_2.tlen = -154
			read_2.qual = "5DDA;DDEC@66DHHHHC=GJJIGJJIGJJJJIIJIHGHIHHHGFFFFBIIJHHGJJIGJJJJJIIHHJIGJJJGJJJJJJJJJIJJJHHHHHFFFDDBBB"
			read_2.tags = read_2.tags + [('XM', 'h...H.....HH......HH...H...H..........H..HH.HHH..HH..HH...H...H..HHH......H..........H..HH.HHH...H..H')] + [('XR', 'CT')] + [('XG', 'GA')]
			return read_1, read_2

		# Build reads
		self.otrse = buildOTSE()
		self.obrse = buildOBSE()
		self.ctotrse = buildCTOTSE()
		self.ctobrse = buildCTOBSE()
		self.otrpe_1, self.otrpe_2 = buildOTPE()
		self.obrpe_1, self.obrpe_2 = buildOBPE()
		self.ctotpe_1, self.ctotpe_2 = buildCTOTPE()
		self.ctobpe_1, self.ctobpe_2 = buildCTOBPE()

	def test_ot_se(self):
		self.assertEqual(get_strand(self.otrse), '+')

	def test_ob_se(self):
		self.assertEqual(get_strand(self.obrse), '-')

	def test_ctot_se(self):
		self.assertEqual(get_strand(self.ctotrse), '+')

	def test_ctob_se(self):
		self.assertEqual(get_strand(self.ctobrse), '-')

	def test_ot_pe(self):
		self.assertEqual(get_strand(self.otrpe_1), '+')
		self.assertEqual(get_strand(self.otrpe_2), '+')

	def test_ob_pe(self):
		self.assertEqual(get_strand(self.obrpe_1), '-')
		self.assertEqual(get_strand(self.obrpe_2), '-')

	def test_ctot_pe(self):
		self.assertEqual(get_strand(self.ctotpe_1), '+')
		self.assertEqual(get_strand(self.ctotpe_2), '+')

	def test_ctob_pe(self):
		self.assertEqual(get_strand(self.ctobpe_1), '-')
		self.assertEqual(get_strand(self.ctobpe_2), '-')

if __name__ == '__main__':
    unittest.main(verbosity=2)
