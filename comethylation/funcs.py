from __future__ import print_function
from .mtuple import *

import re
import csv
import operator
import sys

#### Function definitions ####
def make_ignores_list(ic):
    """Make a list from a string of read positions that are to be ignored.

    Args:
        ic: A string of read positions to ignore. Multiple values should be comma-delimited and ranges can be specified by use of the hyphen, For example:

        '1-5, 80, 98-100'

        corresponds to ignoring read positions 1, 2, 3, 4, 5, 80, 98, 99, 100.

    Returns:
        A Python list of the positions to be ignored.
    """
    if ic is None:
        val = []
    else:
        val = []
        y = [x.strip() for x in ic.split(',')]
        for i in y:
            z = [x.strip() for x in i.split('-')]
            if len(z) == 2:
                val = val + list(range(int(z[0]), int(z[1]) + 1))
            elif len(z) == 1:
                val = val + [int(z[0])]
            else:
                exit_msg = ''.join(['ERROR: -ir1p and -ir2p must be comma-delimited. Ranges can be specified by use of the hyphen, e.g. \'1-5, 80, 98-100\''])
                sys.exit(exit_msg)
        if not all(isinstance(i, int) for i in val):
                exit_msg = ''.join(['ERROR: -ir1p and -ir2p must be comma-delimited. Ranges can be specified by use of the hyphen, e.g. \'1-5, 80, 98-100\''])
                sys.exit(exit_msg)
    return val

def ignore_read_pos(read, methylation_index, ignore_read_pos_list):
    """Ignore methylation loci in a read that appear in the ignore_read_pos_list. A methylation locus may be one of CpG, CHH, CHG or CNN.

    Args:
        read: A pysam.AlignedRead instance.
        methylation_index: A list of zero-based indices. Each index corresponds to the leftmost aligned position of a methylation locus in a read. For example:

        [0, 5]

        corresponds to a read with a methylation locus at the first and sixth positions of the read.
        ignore_read_pos_list: The list of read positions to be ignored.

    Returns:
        An updated version of methylation_index. Will report a warning if the FLAG does not encode whether the read is part of a paired-end or which mate of the paired-end read it is. Will report an error and call sys.exit() if the XR-tag or XG-tag is incompatible or missing.
    """
    # NOTE: Assumes that paired-end reads have FR orientation, which is always true for Bismark but might not be for other aligners
    strand = get_strand(read)
    # Single-end reads
    if not read.is_paired:
        if strand == '+':
            mi_updated = [mi for mi in methylation_index if mi not in ignore_read_pos_list]
        elif strand == '-':
            ignore_read_pos_list = [read.rlen - ic - 1 for ic in ignore_read_pos_list]
            mi_updated = [mi for mi in methylation_index if mi not in ignore_read_pos_list]

    # Paired-end reads: read_1
    elif read.is_paired and read.is_read1:
        if strand == '+':
            mi_updated = [mi for mi in methylation_index if mi not in ignore_read_pos_list]
        elif strand == '-':
            ignore_read_pos_list = [read.rlen - ic - 1 for ic in ignore_read_pos_list]
            mi_updated = [mi for mi in methylation_index if mi not in ignore_read_pos_list]
    # Paired-end reads: read_2
    elif read.is_paired and read.is_read2:
        if strand == '+':
            ignore_read_pos_list = [read.rlen - ic - 1 for ic in ignore_read_pos_list]
            mi_updated = [mi for mi in methylation_index if mi not in ignore_read_pos_list]
        if strand == '-':
            mi_updated = [mi for mi in methylation_index if mi not in ignore_read_pos_list]

    # Return updated methylation_index
    return mi_updated

def ignore_low_quality_bases(read, methylation_index, min_qual, phred_offset):
    """Ignore low quality bases of a read that contribute to a read's methylation_index.

    Args:
        read: A pysam.AlignedRead instance.
        methylation_index: A list of zero-based indices. Each index corresponds to the leftmost aligned position of a methylation locus in a read. For example:

        [0, 5]

        corresponds to a read with a methylation locus at the first and sixth positions of the read.
        min_qual: The minimum base quality (integer). All bases with quality < min_qual are excluded from the returned methylation_index instance.
        phred_offset: The Phred offset of the data (33 or 64).

    Returns:
        An updated version of methylation_index.

    """
    if (min_qual < 0) or (round(min_qual) != min_qual):
        raise ValueError("ignore_low_quality_bases: 'low_qual' must be a positive integer")
    if phred_offset != 33 and phred_offset != 64:
        raise ValueError("ignore_low_quality_bases: 'phred_offset' must be a 33 or 64")

    ignore_these_bases = []
    bqual = bytearray(read.qual)
    for i in methylation_index:
        if (bqual[i] - phred_offset) < min_qual:
            ignore_these_bases.append(i)
    return [x for x in methylation_index if x not in ignore_these_bases]

def fix_old_bismark(read):
	"""Fix the QNAME and FLAG field of a paired-end read from a SAM/BAM file generated by Bismark version < 0.8.3

	Args:
		read: A pysam.AlignedRead instance.

	Returns:
		An updated version of the read.

	"""
	# Strip '/1' or '/2' appended to the end of QNAMEs by Bismark version < 0.8.3. Assumes there are no forward slash characters in the QNAME field
	read.qname = read.qname.split('/')[0]
	# Fix FLAG value
	if read.flag == 67:
		read.flag = 99
	elif read.flag == 115:
		read.flag = 83
	elif read.flag == 131:
		read.flag = 147
	elif read.flag == 179:
		read.flag = 163
	else:
		exit_msg = ''.join(['ERROR: Unexpected FLAG (', str(read.flag), ') for read ', read.qname, 'Sorry, --aligner Bismark_old is unable to deal with this FLAG. Please log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com.'])
		sys.exit(exit_msg)
	return read

def does_read_contain_complicated_cigar(read):
    """Check whether a read contains a complicated CIGAR string character, defined as anything other than a match (M; 0), insertion (I; 1), deletion (D; 2), soft-clip (S, 4) or hard-clip (H, 5).

    Args:
        read: A pysam.AlignedRead instance.

    Returns:
        True if read contains an complicated CIGAR string character, False otherwise.
    """
    val = any([x[0] not in [0, 1, 2, 4, 5] for x in read.cigar])
    return val

def extract_and_update_methylation_index_from_single_end_read(read, BAM, methylation_m_tuples, m, methylation_type, methylation_pattern, ignore_read_1_pos, min_qual, phred_offset, ob_strand_offset):
    """Extracts m-tuples of methylation loci from a single-end read and adds the comethylation m-tuple to the methylation_m_tuples object.

    Args:
        read: An AlignedRead instance corresponding to a single-end read.
        BAM: The Samfile instance corresponding to the sample. Required in order to extract chromosome names from read.
        methylation_m_tuples: An MTuple instance.
        methylation_type: A string of the methylation type, e.g. CG for CpG methylation. Must be a valid option for the MTuple class.
        methylation_pattern: A regular expression of the methylation loci, e.g. '[Zz]' for CpG-methylation
        m: Is the "m" in "m-tuple", i.e. the size of the m-tuple. m must be an integer greater than or equal to 1. WARNING: No error or warning produced if this condition is violated.
        ignore_read_1_pos: Ignore this list of read positions from each read.
        min_qual: Ignore bases with quality-score less than this value.
        phred_offset: The offset in the Phred scores. Phred33 corresponds to phred_offset = 33 and Phred64 corresponds to phred_offset 64.
        ob_strand_offset: How many bases a methylation loci on the OB-strand must be moved to the left in order to line up with the C on the OT-strand; e.g. ob_strand_offset = 1 for CpGs.
    Returns:
        methylation_m_tuples: An updated version of methylation_m_tuples.
        n_methylation_loci: The number of methylation loci extracted from the read.
    """
    # Identify methylation events in read, e.g. CpGs or CHHs. The methylation_pattern is specified by a command line argument (e.g. Z/z corresponds to CpG)
    methylation_index = [midx.start() for midx in re.finditer(methylation_pattern, read.opt('XM'))]
    # Ignore any read positions specified in ignore_read_1_pos
    methylation_index = ignore_read_pos(read, methylation_index, ignore_read_1_pos)
    # Ignore any positions with a base quality less than min_qual
    methylation_index = ignore_low_quality_bases(read, methylation_index, min_qual, phred_offset)
    n_methylation_loci = len(methylation_index)
    strand = get_strand(read)

    # Call methylation m-tuples if there are sufficient methylation loci in the read.
    if n_methylation_loci >= m:
      # Convert 0-based positions to 1-based positions.
      # This will break if get_positions(read)[x] includes None, but this is intended (although it will lead to a cryptic error message).
      positions = [get_positions(read)[x] + 1 for x in methylation_index]
      # If read is informative for the OB-strand then translate co-ordinate "ob_strand_offset" bases to the left so that it points to the C on the OT-strand of the methylation locus (will only have an effect if doing strand-specific methylation calling, in which case ob_strand_offset != 0).
      if strand == '-':
          positions = [x - ob_strand_offset for x in positions]
      # Exit if methylation loci are incorrectly ordered
      if not positions == sorted(positions):
          exit_msg = ' '.join(["ERROR: The positions of the methylation loci are not properly ordered for single-end read", read.qname, "\n'positions' =", str(positions), '.\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
          sys.exit(exit_msg)
      # Construct each bookended methylation-loci m-tuple and add it to the methylation_m_tuple object.
      # For a read containing k methylation loci there are (k - m + 1) m-tuples.
      for i in range(0, len(methylation_index) - m + 1):
          this_comethylation_pattern = ''.join([read.opt('XM')[j] for j in methylation_index[i:(i + m)]])
          # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
          if ob_strand_offset != 0:
              mt_strand = '*'
          else:
              mt_strand = strand
          this_m_tuple_positions = (BAM.getrname(read.tid),) + (mt_strand, ) + tuple(positions[i:(i + m)])
          methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern, read, None)
    return methylation_m_tuples, n_methylation_loci

def extract_and_update_methylation_index_from_paired_end_reads(read_1, read_2, BAM, methylation_m_tuples, m, methylation_type, methylation_pattern, ignore_read_1_pos, ignore_read_2_pos, min_qual, phred_offset, ob_strand_offset, overlap_check, n_fragment_skipped_due_to_bad_overlap, FAILED_QC):
    """Extracts m-tuples of methylation loci from a readpair and adds the comethylation m-tuple to the methylation_m_tuples object.

    Args:
        read_1: An AlignedRead instance corresponding to read_1 of the readpair.
        read_2: An AlignedRead instance corresponding to read_2 of the readpair.
        BAM: The Samfile instance corresponding to the sample. Required in order to extract chromosome names from read.
        methylation_m_tuples: An MTuple instance.
        m: Is the "m" in "m-tuple", i.e. the size of the m-tuple. m must be an integer greater than or equal to 1. WARNING: No error or warning produced if this condition is violated.
        methylation_type: A string of the methylation type, e.g. CG for CpG methylation. Must be a valid option for the MTuple class.
        methylation_pattern: A regular expression of the methylation loci, e.g. '[Zz]' for CpG-methylation
        ignore_read_1_pos: Ignore this list of positions from each read_1.
        ignore_read_2_pos: Ignore this list of positions from each read_2.
        min_qual: Ignore bases with quality-score less than this value.
        phred_offset: The offset in the Phred scores. Phred33 corresponds to phred_offset = 33 and Phred64 corresponds to phred_offset 64.
        ob_strand_offset: How many bases a methylation loci on the OB-strand must be moved to the left in order to line up with the C on the OT-strand; e.g. ob_strand_offset = 1 for CpGs.
        overlap_check: The type of check to be performed (listed by most-to-least stringent): check the entire overlapping sequence is identical (sequence), check the XM-tag is identical for the overlapping region (XM), do no check of the overlapping bases but use the read with the higher quality basecalls in the overlapping region (quality), or simply use the overlapping bases from read_1 ala bismark_methylation_extractor (Bismark)
        n_fragment_skipped_due_to_bad_overlap: The total number of fragments (readpairs) skipped due to the overlapping sequencing not passing the filter.
        FAILED_QC: The file object where the QNAME of readpairs that fail the overlap check are written, along with the reason the readpairs failed.
    Returns:
        methylation_m_tuples: An updated version of methylation_m_tuples.
        n_methylation_loci: The number of methylation loci extracted from the read.
    """
    # Identify methylation events in read, e.g. CpGs or CHHs. The methylation_pattern is specified by a command line argument (e.g. Z/z corresponds to CpG)
    methylation_index_1 = [midx.start() for midx in re.finditer(methylation_pattern, read_1.opt('XM'))]
    methylation_index_2 = [midx.start() for midx in re.finditer(methylation_pattern, read_2.opt('XM'))]

    # Ignore any read positions specified in ignore_read_1_pos or ignore_read_1_pos
    methylation_index_1 = ignore_read_pos(read_1, methylation_index_1, ignore_read_1_pos)
    methylation_index_2 = ignore_read_pos(read_2, methylation_index_2, ignore_read_2_pos)
    # Ignore any positions with a base quality less than min_qual
    methylation_index_1 = ignore_low_quality_bases(read_1, methylation_index_1, min_qual, phred_offset)
    methylation_index_2 = ignore_low_quality_bases(read_2, methylation_index_2, min_qual, phred_offset)
    # Check strand of each mate make sense
    strand_1 = get_strand(read_1)
    strand_2 = get_strand(read_2)
    # Process read-pairs to handle overlapping mates.
    methylation_index_1, methylation_index_2, fragment_skipped = process_overlap(read_1, read_2, methylation_index_1, methylation_index_2, overlap_check, FAILED_QC)
    n_fragment_skipped_due_to_bad_overlap = n_fragment_skipped_due_to_bad_overlap + fragment_skipped
    n_methylation_loci = len(methylation_index_1) + len(methylation_index_2)

    # Call methylation m-tuples if there are sufficient methylation loci in the read-pair.
    if n_methylation_loci >= m:
      # Convert 0-based positions to 1-based positions.
      # This will break if get_positions(read)[x] includes None, but this is intended (although it will lead to a cryptic error message).
      positions_1 = [get_positions(read_1)[x] + 1 for x in methylation_index_1]
      positions_2 = [get_positions(read_2)[x] + 1 for x in methylation_index_2]

      if any(x in positions_1 for x in positions_2):
          exit_msg = ''.join(['ERROR: For readpair ', read_1.qname, ', position_1 and position_2 contain a common position. This should not happen.\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
          sys.exit(exit_msg)
        # Case 1: Readpair is informative for OT-strand
      if strand_1 == '+' and strand_2 == '+':
          # Exit if methylation loci are incorrectly ordered
          if positions_1 + positions_2 != sorted(positions_1 + positions_2):
              exit_msg = ' '.join(["ERROR: The positions of the methylation loci are not properly ordered for paired-end read", read_1.qname, ", which is informative for the OT-strand.\n'positions_1 + positions_2' =", str(positions_1 + positions_2), '\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
              sys.exit(exit_msg)
          # Firstly, create all m-tuples of methylation loci where each locus is from read_1.
          if len(methylation_index_1) >= m:
              # For a read containing k methylation loci there are (k - m + 1) m-tuples.
              for i in range(0, len(methylation_index_1) - m + 1):
                  this_comethylation_pattern = ''.join([read_1.opt('XM')[j] for j in methylation_index_1[i:(i + m)]])
                  # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
                  if ob_strand_offset != 0:
                      mt_strand = '*'
                  else:
                      mt_strand = strand_1
                  this_m_tuple_positions = (BAM.getrname(read_1.tid),) + (mt_strand, ) + tuple(positions_1[i:(i + m)])
                  methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern, read_1, read_2)
          # Secondly, create all m-tuples of methylation loci where the leftmost locus is on read_1 and the rightmost locus is on read_2.
          num_shared_m_tuples = max(len(methylation_index_1) + len(methylation_index_2) - m + 1, 0) - max(len(methylation_index_1) - m + 1, 0) - max(len(methylation_index_2) - m + 1, 0)
          # The index of the leftmost locus to be part of a "shared" m-tuple. The rightmost_shared_locus_index, min(m - 2, len(methylation_index_2) - 1), is not required.
          leftmost_shared_locus_index = max(0, len(methylation_index_1) - m + 1)
          for i in range(0, num_shared_m_tuples):
              this_m_tuple_positions_1 = positions_1[(leftmost_shared_locus_index + i):]
              this_m_tuple_positions_2 = positions_2[:(m - len(this_m_tuple_positions_1))]
              # Exit if methylation loci are incorrectly ordered. While a similar check is performed a few lines above, this is a sanity check to make sure than nothing has gone wrong in constructing the shared m-tuples
              if this_m_tuple_positions_1 + this_m_tuple_positions_2 != sorted(this_m_tuple_positions_1 + this_m_tuple_positions_2):
                  exit_msg = ' '.join(["ERROR: The positions of the shared methylation loci are not properly ordered for paired-end read", read_1.qname, ", which is informative for the OT-strand.\n'this_m_tuple_positions_1 + this_m_tuple_positions_2' =", str(this_m_tuple_positions_1 + this_m_tuple_positions_2), '\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
                  sys.exit(exit_msg)
              this_comethylation_pattern = ''.join([read_1.opt('XM')[j] for j in methylation_index_1[(leftmost_shared_locus_index + i):]] + [read_2.opt('XM')[j] for j in methylation_index_2[:(m - len(this_m_tuple_positions_1))]])
              # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
              if ob_strand_offset != 0:
                  mt_strand = '*'
              else:
                  mt_strand = strand_1
              this_m_tuple_positions = (BAM.getrname(read_1.tid),) + (mt_strand, ) + tuple(this_m_tuple_positions_1) + tuple(this_m_tuple_positions_2)
              methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern,  read_1, read_2)
          # Finally, create all m-tuples of methylation loci where each locus is from read_2.
          if len(methylation_index_2) >= m:
              # For a read containing k methylation loci there are (k - m + 1) m-tuples.
              for i in range(0, len(methylation_index_2) - m + 1):
                  this_comethylation_pattern = ''.join([read_2.opt('XM')[j] for j in methylation_index_2[i:(i + m)]])
                  # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
                  if ob_strand_offset != 0:
                      mt_strand = '*'
                  else:
                      mt_strand = strand_1
                  this_m_tuple_positions = (BAM.getrname(read_2.tid),) + (mt_strand, ) + tuple(positions_2[i:(i + m)])
                  methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern, read_1, read_2)

      # Case 2: Readpair is informative for OB-strand
      elif strand_1 == '-' and strand_2 == '-':
          # Translate co-ordinates "ob_strand_offset" bases to the left so that it points to the C on the OT-strand of the methylation locus
          positions_1 = [x - ob_strand_offset for x in positions_1]
          positions_2 = [x - ob_strand_offset for x in positions_2]
          # Exit if methylation loci are incorrectly ordered.
          if positions_2 + positions_1 != sorted(positions_2 + positions_1):
              exit_msg = ' '.join(["ERROR: The positions of the methylation loci are not properly ordered for paired-end read", read_1.qname, "which is informative for the OB-strand.\n'positions_2 + positions_1' =", str(positions_2 + positions_1), '\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
              sys.exit(exit_msg)
          # Firstly, create all m-tuples of methylation loci where each locus is from read_1.
          if len(methylation_index_1) >= m:
              # For a read containing k methylation loci there are (k - m + 1) m-tuples.
              for i in range(0, len(methylation_index_1) - m + 1):
                  this_comethylation_pattern = ''.join([read_1.opt('XM')[j] for j in methylation_index_1[i:(i + m)]])
                  # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
                  if ob_strand_offset != 0:
                      mt_strand = '*'
                  else:
                      mt_strand = strand_1
                  this_m_tuple_positions = (BAM.getrname(read_1.tid),) + (mt_strand, ) + tuple(positions_1[i:(i + m)])
                  methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern,  read_1, read_2)
          # Secondly, create all m-tuples of methylation loci where the leftmost locus is on read_1 and the rightmost locus is on read_2
          num_shared_m_tuples = max(len(methylation_index_1) + len(methylation_index_2) - m + 1, 0) - max(len(methylation_index_1) - m + 1, 0) - max(len(methylation_index_2) - m + 1, 0)
          # The index of the leftmost locus to be part of a "shared" m-tuple. The rightmost_shared_locus_index, min(m - 2, len(methylation_index_1) - 1), is not required.
          leftmost_shared_locus_index = max(0, len(methylation_index_2) - m + 1)
          for i in range(0, num_shared_m_tuples):
              this_m_tuple_positions_2 = positions_2[(leftmost_shared_locus_index + i):]
              this_m_tuple_positions_1 = positions_1[:(m - len(this_m_tuple_positions_2))]
              # Exit if methylation loci are incorrectly ordered. While a similar check is performed a few lines above, this is a sanity check to make sure than nothing has gone wrong in constructing the shared m-tuples
              if this_m_tuple_positions_2 + this_m_tuple_positions_1 != sorted(this_m_tuple_positions_2 + this_m_tuple_positions_1):
                  exit_msg = ' '.join(["ERROR: The positions of the shared methylation loci are not properly ordered for paired-end read", read_1.qname, "which is aligned to the OB-strand.\n'this_m_tuple_positions_2 + this_m_tuple_positions_1' =", str(this_m_tuple_positions_2 + this_m_tuple_positions_1), '\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
                  sys.exit(exit_msg)
              this_comethylation_pattern = ''.join([read_2.opt('XM')[j] for j in methylation_index_2[(leftmost_shared_locus_index + i):]] + [read_1.opt('XM')[j] for j in methylation_index_1[:(m - len(this_m_tuple_positions_2))]])
              # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
              if ob_strand_offset != 0:
                  mt_strand = '*'
              else:
                  mt_strand = strand_1
              this_m_tuple_positions = (BAM.getrname(read_1.tid),) + (mt_strand, ) + tuple(this_m_tuple_positions_2) + tuple(this_m_tuple_positions_1)
              methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern, read_1, read_2)
          # Finally, create all m-tuples of methylation loci where each locus is from read_2.
          if len(methylation_index_2) >= m:
              # For a read containing k methylation loci there are (k - m + 1) m-tuples.
              for i in range(0, len(methylation_index_2) - m + 1):
                  this_comethylation_pattern = ''.join([read_2.opt('XM')[j] for j in methylation_index_2[i:(i + m)]])
                  # Set the m-tuple strand (mt_strand) as '*' if ob_strand_offset != 0 (which is True if --strand-collapse is set)
                  if ob_strand_offset != 0:
                      mt_strand = '*'
                  else:
                      mt_strand = strand_1
                  this_m_tuple_positions = (BAM.getrname(read_2.tid),) + (mt_strand, ) + tuple(positions_2[i:(i + m)])
                  methylation_m_tuples.increment_count(this_m_tuple_positions, this_comethylation_pattern, read_1, read_2)
      else:
          exit_msg = ''.join(['ERROR: The informative strands for readpair ', read_1.qname, ',  do not agree between mates. This should not happen.\nPlease log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
          sys.exit(exit_msg)
    return methylation_m_tuples, n_methylation_loci, n_fragment_skipped_due_to_bad_overlap

def write_methylation_m_tuples_to_file(methylation_m_tuples, OUT):
    """Write the methylation_m_tuples instance to a tab-separated file. The m-tuples are ordered by chromosome and genomic co-ordinates.

    Args:
        methylation_m_tuples: An MTuple instance.
        OUT: The file to write output to.
    """
    # tab_writer writes a tab-separated output file to the filehandle OUT
    tab_writer = csv.writer(OUT, delimiter='\t', quotechar=' ', quoting=csv.QUOTE_MINIMAL)

    # Get m
    m = methylation_m_tuples.m
    # Create the header row and write to file
    header = ['chr'] + ['strand'] + ['pos' + str(i) for i in range(1, m + 1)] + methylation_m_tuples.comethylation_patterns
    tab_writer.writerow(header)
    # Sort methylation_m_tuples.mtuples.keys() by chromosome (using methylation_m_tuples.chr_map for sort order), then by strand ('+' > '-' > '*') and finally by positions (pos1, pos2, ... to posm)
    for this_m_tuple in sorted(list(methylation_m_tuples.mtuples.keys()), key = lambda x: (methylation_m_tuples.chr_map[x[0]], ) + ({'+': 1, '-': 2, '*': 3}[x[1]], ) + tuple(x[2:])):
        row = this_m_tuple + tuple(methylation_m_tuples.mtuples[this_m_tuple])
        tab_writer.writerow(row)

def get_strand(read):
    """
    Report whether a read is informative for the OT-strand or OB-strand.
    Currently using a strict check that ensures the reads are in the expected orientation for the given strand.
    See commented out lines for a less-strict version.
    Will report an error and call sys.exit() if the XR-tag or XG-tag is incompatible or missing.

    Args:
        read: A pysam.AlignedRead instance with XR-tag and XG-tag.
    Returns:
        strand: For which strand the read/readpair is informative: '+' (OT, original-top, Watson) or '-' (OB, original-bottom, Crick)
    """
    ## Single-end
    if not read.is_paired:
        ## Check if aligned to OT- or CTOT-strand, i.e., informative for OT-strand.
        if (read.opt('XR') == 'CT' and read.opt('XG') == 'CT') or (read.opt('XR') == 'GA' and read.opt('XG') == 'CT'):
        # if read_1.opt('XG') == 'CT'
            strand = '+'
        ## Else, check if aligned to OB- or CTOB-strand, i.e., informative for OB-strand.
        elif (read.opt('XR') == 'CT' and read.opt('XG') == 'GA') or (read.opt('XR') == 'GA' and read.opt('XG') == 'GA'):
        # elif read_1.opt('XG') == 'GA'
            strand = '-'
        ## Else, something odd about this read
        else:
            exit_msg = ''.join(['ERROR: Read ', read.qname, ' has incompatible or missing XG-tag or XR-tag. Please log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
            sys.exit(exit_msg)
    ## Paired-end
    elif read.is_paired:
        if read.is_read1:
            ## Check if aligned to CT- or CTOT-strand, i.e., informative for OT-strand.
            if (read.opt('XR') == 'CT' and read.opt('XG') == 'CT') or (read.opt('XR') == 'GA' and read.opt('XG') == 'CT'):
            #if read.opt('XG') == 'CT':
                strand = '+'
            ## Else, check if aligned to OB- or CTOB-strand, i.e., informative for OB-strand.
            elif (read.opt('XR') == 'CT' and read.opt('XG') == 'GA') or (read.opt('XR') == 'GA' and read.opt('XG') == 'GA'):
            #elif read.opt('XG') == 'GA':
                strand = '-'
            ## Else, something odd about this read
            else:
                exit_msg = ''.join(['ERROR: Read ', read.qname, ' has incompatible or missing XG-tag or XR-tag. Please log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
                sys.exit(exit_msg)
        elif read.is_read2:
            ## Check if aligned CT or CTOT-strand, i.e., informative for OT-strand.
            if (read.opt('XR') == 'GA' and read.opt('XG') == 'CT') or (read.opt('XR') == 'CT' and read.opt('XG') == 'CT'):
                strand = '+'
            ## Else, check if aligned OB- or CTOB-strand, i.e., informative for OB-strand.
            elif (read.opt('XR') == 'GA' and read.opt('XG') == 'GA') or (read.opt('XR') == 'CT' and read.opt('XG') == 'GA'):
                strand = '-'
            ## Else, something odd about this read
            else:
                exit_msg = ''.join(['ERROR: Read ', read.qname, ' has incompatible or missing XG-tag or XR-tag. Please log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
                sys.exit(exit_msg)
    else:
        exit_msg = ''.join(['ERROR: Read ', read.qname, ' is neither a single-end read nor part of a paired-end read. Please log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com'])
    return strand

# TODO: Check that get_positions() works with soft-clipped reads. If this function handles soft-clipped reads correctly then comethylation can process soft-clipped reads (provided the XM-tag is has '.' for soft-clipped positions and read.seq, read.qual, read.opt('XM') and get_positions(read) are all of the same length and equal to the sequence length).
# TODO: It should be possible to write a faster version of this using C-level (via Cython?) operations, e.g., see how aligned_pairs is defined. Awaiting reply to issue posted to pysam GitHub issue tracker (16/07/2014).
def get_positions(read):
  """Get reference-based positions of all bases in a read, whether aligned or not, and allowing for inserted and soft-clipped bases.

  Args:
      read: A pysam.AlignedRead instance.

  Returns:
      A list of positions equal in length to read.seq. The result is identical to read.positions if the read does not contain any insertions or soft-clips. Read-positions that are insertions or soft-clips have None as the corresponding entry in the returned list.
  """
  # Check read actually has CIGAR
  if read.cigar is None:
    # No CIGAR string so positions must be [] because there is no alignment.
    positions = []
  else:
    # From the SAM spec (http://samtools.github.io/hts-specs/SAMv1.pdf), "S may only have H operations between them and the ends of the CIGAR string".
    n = len(read.cigar)
    # If first CIGAR operation is H (5), check whether second is S (4).
    if read.cigar[0][0] == 5:
      if n > 1:
        if read.cigar[1][0] == 4:
          positions = [None] * read.cigar[1][1]
        else:
          positions = []
    # Check if first CIGAR operation is S (4).
    elif read.cigar[0][0] == 4:
      positions = [None] * read.cigar[0][1]
    # Otherwise there can't be any leftmost soft-clipping.
    else:
      positions = []
    # Add "internal" read-positions, which are only made up of positions with M/I/D CIGAR operations and so can be extracted from read.aligned_pairs.
    positions = positions + [y[1] for y in read.aligned_pairs if y[0] is not None]
    # If last CIGAR operation is H (5), check whether second-last is S (4).
    if read.cigar[n - 1][0] == 5:
      if n > 1:
        # If second-last positions is S (4), then need to pad but otherwise nothing to do (and also no need for "closing" else).
        if read.cigar[n - 2][0] == 4:
          positions = positions + [None] * read.cigar[n - 2][1]
    # Check if last CIGAR operation is S (4).
    elif read.cigar[n - 1][0] == 4:
      positions = positions + [None] * read.cigar[n - 1][1]

    # Sanity check that length of positions is equal to length of read.seq
    if (len(read.seq) != len(positions)):
      exit_msg = ''.join(['Length of positions (', str(len(positions)), ') does not equal length of read.seq (', str(len(read.seq)), ') for read: ', read.qname, '\nThis should never happen. Please log an issue at www.github.com/PeteHaitch/comethylation describing the error or email me at peter.hickey@gmail.com.'])
      sys.exit(exit_msg)
  return positions

# TODO: Check that process_overlap() works with soft-clipped reads, particularly that "overlapping" soft-clips are properly handled. Can't check this until I have some data aligned with an aligner that allows soft-clips, e.g. bwa-meth, as Bismark does not allow them.
def process_overlap(read_1, read_2, methylation_index_1, methylation_index_2, overlap_check, FAILED_QC):
  """Identify any overlapping bases between read_1 and read_2 and remove these from methylation_index_1 or methylation_index_2 according to the option specified by overlap_check.

  Args:
      read_1: A pysam.AlignedRead instance with read.is_read1 == true. Must be paired with read_2.
      read_2: A pysam.AlignedRead instance with read.is_read2 == true. Must be paired with read_1.
      methylation_index_1: A list of zero-based indices.  Each index corresponds to the leftmost aligned position of a methylation locus in read_1. For example:

      [0, 5]

      corresponds to read_1 with a methylation locus at the first and sixth positions of the read.
      methylation_index_2: As for methylation_index_1 but informative for read_2.
      overlap_check: The type of check to be performed (listed from most-to-least stringent):
      1. Check that the entire overlapping sequence is identical; if not identical then do not use any methylation calls from the entire read-pair (sequence_strict).
      2. Check that the entire overlapping sequence is identical; if not identical then do not use any methylation calls from the overlap (sequence).
      3. Check that the XM-tag is identical for the overlapping region; if not identical then do not use any methylation calls from the entire read-pair (XM_strict).
      4. Check that the XM-tag is identical for the overlapping region; if not identical then do not use any methylation calls from the overlap (XM).
      5. Check that the XM-tag is identifal for the overlapping region; if not identical then exclude those positions of disagreement and count once the remaining positions in the overlap (XM_ol).
      6. No check of the overlapping bases; simply use the read with the higher average quality basecalls in the overlapping region (quality).
      7. No check of the overlapping bases; simply use the overlapping bases from read_1, i.e., the method used by bismark_methylation_extractor (Bismark).
      FAILED_QC: The file object where the QNAME of readpairs that fail the overlap check are written, along with the reason the readpairs failed.

  Returns:
      Updated versions of methylation_index_1 and methylation_index_2.
  """
  # Get read positions
  positions_1 = get_positions(read_1)
  positions_2 = get_positions(read_2)

  # Flag indicating whether the entire fragment was skipped (only used if overlap_check is sequence_strict of XM_strict)
  fragment_skipped = 0

  # Creating the overlap is a two-step process. (1) Find the intersection of positions_1 and positions_2 (excluding None positions); (2) Define the overlap as all positions between the smallest element and largest element of the overlap set.
  # The second step is necessary because there may be bases in the overlap where one of the reads has a deletion. For example, consider the following overlap (ol) of read_1 (r1) and read_2 (r2) using "=" to represent aligned bases, "x" to represent deletions and "+" to represent insertions and soft-clips:
  # ol:  |----|
  # r1: ==xx===
  # r2:  =========
  # The overlap is 6bp long but r1 has a deletion of 2bp. While this is arguably a bad alignment, it does occur in practice and so needs to be appropriately dealt with.
  # It is very difficult to identify the boundary of an overlap if there are insertions or soft-clipped bases near the ends. For example:
  # ol:      |-|
  # r1: ==+++===
  # r2:    ++======
  # The start of this overlap (leftmost position) doesn't map to this position in the reference genome. Furthermore, the leftmost base of r2 might be soft-clipped
  # I don't know whether this can actually occur in practice. And perhaps it can be resolved with CIGAR operations but it's going to be very fiddly and, quite frankly, I've spent enough time on what I believe to be a very rare problem.
  # Therefore, for simplicity, I define the overlap by the leftmost and rightmost positions that have a position in the reference genome. So, if the overlap is an insertion (resp. soft-clip) then there is, not quite correctly (resp. correctly), no overlap by this method.

  # Have to compute the overlap using the second, more-complicated method because if there is a deletion at the end of the overlap then the first method will miss it.
  #overlap = set(positions_1) & set(positions_2) - set([None])
  overlap = set(list(range(min(positions_1), max(positions_1) + 1))) & set(list(range(min(positions_2), max(positions_2) + 1)))

  # Check whether there is any overlap.
  # There's either (1a) no overlap,(1b) the overlap is an insertion or (2) an overlap. In the case of (1a) there is nothing to do and in the case of (1b) I have decided it's too hard and rare to be worth dealing with.
  if len(overlap) != 0:
    # Get the leftmost (start) and rightmost (end) positions of the overlap with respect to the reference genome co-ordinates.
    start_ol = min(overlap)
    end_ol = max(overlap)

    # Get the read-positions (indices of the positions in each read) that are in the overlap. These are used for slicing out the overlap from read elements such as seq, qual and XM-tag.
    start_ol_1 = [idx for idx, value in enumerate(positions_1) if value >= start_ol and value is not None][0]
    end_ol_1 = [idx for idx, value in enumerate(positions_1) if value <= end_ol and value is not None][-1]
    start_ol_2 = [idx for idx, value in enumerate(positions_2) if value >= start_ol and value is not None][0]
    end_ol_2 = [idx for idx, value in enumerate(positions_2) if value <= end_ol and value is not None][-1]

    if overlap_check == "sequence_strict":
      if read_1.seq[start_ol_1:(end_ol_1 + 1)] != read_2.seq[start_ol_2:(end_ol_2 + 1)]:
        # Kill the read-pair
        methylation_index_1 = []
        methylation_index_2 = []
        fragment_skipped = 1
        failed_read_msg = '\t'.join([read_1.qname, ''.join(['failed the --overlap-filter ', overlap_check, '\n'])])
        FAILED_QC.write(failed_read_msg)
      else:
        # Retain only those elements of methylation_index_2 that are outside the overlap.
        # Choice of trimming methylation_index_1 or methylation_index_2 is arbitrary because if the seq are identical in the overlap then there is no reason to choose read_1 over read_2 and vice versa.
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
    elif overlap_check == "sequence":
      if read_1.seq[start_ol_1:(end_ol_1 + 1)] != read_2.seq[start_ol_2:(end_ol_2 + 1)]:
        # Retain only those elements of methylation_index_1 and methylation_index_2 that are outside the overlap.
        methylation_index_1 = [i for i in methylation_index_1 if i < start_ol_1 or i > end_ol_1]
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
      else:
        # Retain only those elements of methylation_index_2 that are outside the overlap.
        # Choice of trimming methylation_index_1 or methylation_index_2 is arbitrary because if the seq are identical in the overlap then there is no reason to choose read_1 over read_2 and vice versa.
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
    elif overlap_check == "XM_strict":
      if read_1.opt('XM')[start_ol_1:(end_ol_1 + 1)] != read_2.opt('XM')[start_ol_2:(end_ol_2 + 1)]:
        # Kill the read-pair
        methylation_index_1 = []
        methylation_index_2 = []
        fragment_skipped = 1
        failed_read_msg = '\t'.join([read_1.qname, ''.join(['failed the --overlap-filter ', overlap_check, '\n'])])
        FAILED_QC.write(failed_read_msg)
      else:
        # Retain only those elements of methylation_index_2 that are outside the overlap.
        # Choice of trimming methylation_index_1 or methylation_index_2 is arbitrary because if the XM-tags are identical in the overlap then there is no reason to choose read_1 over read_2 and vice versa.
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
    elif overlap_check == "XM":
      if read_1.opt('XM')[start_ol_1:(end_ol_1 + 1)] != read_2.opt('XM')[start_ol_2:(end_ol_2 + 1)]:
        # Retain only those elements of methylation_index_1 and methylation_index_2 that are outside the overlap.
        methylation_index_1 = [i for i in methylation_index_1 if i < start_ol_1 or i > end_ol_1]
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
      else:
        # Retain only those elements of methylation_index_2 that are outside the overlap.
        # Choice of trimming methylation_index_1 or methylation_index_2 is arbitrary because if the XM-tags are identical in the overlap then there is no reason to choose read_1 over read_2 and vice versa.
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
    elif overlap_check == 'XM_ol':
      # Make every methylation call in the overlap a single copy by (1) only retaining those elements of methylation_index_2 that are outside the overlap and (2) only retaining those elements of methylation_index_1 where the XM-tag value agree for read_1 and read_2.
      methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
      # The check_XM_overlap function is necessary because using positions_2.index(positions_1[i]) will return a ValueError if the positions_1[i] can't be found in positions_2 and so I need an try-except to handle this.
      def check_XM_overlap(i, read_1, read_2, positions_1, positions_2):
         try:
             return read_1.opt('XM')[i] == read_2.opt('XM')[positions_2.index(positions_1[i])]
         except ValueError:
             return False
      methylation_index_1 = [i for i in methylation_index_1 if i < start_ol_1 or i > end_ol_1 or check_XM_overlap(i, read_1, read_2, positions_1, positions_2)]
    elif overlap_check == "quality":
      # Compute the average base quality in the overlap. Can't simply compare sums because one read may have more bases in the overlapping region than the other (e.g. see above example when computing the overlap)
      bqual_1 = bytearray(read_1.qual[start_ol_1:(end_ol_1 + 1)])
      bqual_2 = bytearray(read_2.qual[start_ol_2:(end_ol_2 + 1)])
      if (sum(bqual_1) / float(len(bqual_1))) >= (sum(bqual_2) / float(len(bqual_2))):
        # Retain only those elements of methylation_index_2 that are outside the overlap.
        methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
      else:
        # Retain only those elements of methylation_index_1 that are outside the overlap.
        methylation_index_1 = [i for i in methylation_index_1 if i < start_ol_1 or i > end_ol_1]
    elif overlap_check == "Bismark":
      #  Retain only those elements of methylation_index_2 that are outside the overlap; bismark_methylation_extractor always uses read_1 instead of read_2 when there is an overlap.
      methylation_index_2 = [i for i in methylation_index_2 if i < start_ol_2 or i > end_ol_2]
    else:
      raise ValueError("process_overlap: 'overlap_check' must be one of 'sequence_strict', 'sequence', 'XM_strict', 'XM', 'XM_ol', 'quality' or 'Bismark'")
  return methylation_index_1, methylation_index_2, fragment_skipped

__all__ = [
    'make_ignores_list',
    'ignore_read_pos',
    'ignore_low_quality_bases',
    'fix_old_bismark',
    'does_read_contain_complicated_cigar',
    'extract_and_update_methylation_index_from_single_end_read',
    'extract_and_update_methylation_index_from_paired_end_reads',
    'write_methylation_m_tuples_to_file',
    'get_strand',
    'get_positions',
    'process_overlap'
]
