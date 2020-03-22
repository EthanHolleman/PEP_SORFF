import subprocess
import os

from io_utils import convert_genome_to_list, if_not_exists_make, parse_gff, convert_genome_to_header_dict
from sequence import Sequence


class Genome():
    '''
    Representation of an individual bacterial genome. Stores its sequence files
    and has methods for predicting coding regions and then retreiving
    non-coding regions

    :param genome_file: string, filepath to fasta formated file of the complete bacterial genome
    :param phenotype: string, string that acts as a key for identifying the bacterial phenotype
    :param gene_prediction_file: string, filepath to gff generated via prokka. Default = None
    :param non_coding_file: string, filepath to fasta of non-coding regions. Default = None
    '''

    def __init__(self, genome_file, phenotype, gene_prediction_file=None, non_coding_file=None):
        self.genome_file = genome_file
        self.phenotype = phenotype
        self.gene_prediction_file = gene_prediction_file
        self.non_coding_file = non_coding_file
        self.non_coding_seqs = []
        # potentially change to dictionary to allow non coding seq
        # look up by start location if that is needed later

    def __repr__(self):
        '''
        Determines what is returned when a genome object is printed.
        '''
        s = ['Phenotype:', str(self.phenotype), 'Genome File:', str(self.genome_file),
             'Gene Prediction File:', str(self.gene_prediction_file),
             'Non-coding File:', str(self.non_coding_file),
             'Num non-coding seqs:', str(len(self.non_coding_seqs))]
        return ' '.join(s)

    def __len__(self):
        return len(self.non_coding_seqs)

    def make_gene_predictions(self, output_dir, threads, path_to_exec='prokka',
                              results_dir_name='prokka_results'):
        '''
        This function will run prokka to find predicted gene locations for
        the instance of Genome it is called on.
        '''
        # TODO: Get this function woring with correct variable names
        # and output paths organized
        # will need to make new folder for prokka results for each genome
        # that runs gene prediction
        pass
        prokka_dir = if_not_exists_make(output_dir, results_dir_name)

        input_file = self.genome_file

        cmd = [path_to_exec, '--outdir', prokka_dir,
               '--cpus', str(threads), '--force', input_file]
        subprocess.call(cmd)

        return prokka_dir
    # run gene prediction methods here

    def get_non_coding_regions(self):
        # may have to modify if genomes are not all on one chromosome
        '''
        Using the genome file associated with an instance of a specific genome
        object and the gene prediction gff file to extract the non-coding
        regions in the genome. Will write the non-coding strings as a fasta
        file and store the path to that file in the non_coding_file
        attribute.
        '''
        coding_regions = parse_gff(self.gene_prediction_file, 0, 3, 4)
        # read the gff file for predicted coding regions

        coding_regions_dict = {}

        # make dictionary based on sequence headers. Each header key is mapped
        # to a list of tuples. Each tuple contains the start and stop location
        # for a predicted gene

        genome = convert_genome_to_header_dict(self.genome_file)

        for header, start, stop in coding_regions:
            start, stop = int(start), int(stop)
            if header in coding_regions_dict:
                coding_regions_dict[header].append((start, stop))
            else:
                coding_regions_dict[header] = [(start, stop)]

        for header, coding_regions_list in coding_regions_dict.items():
            working_seq = genome[header]
            cur_non_coding_string = ''
            i, j = 0, 0
            start, stop = coding_regions_list[j]
            while True:
                if i < start:
                    cur_non_coding_string += working_seq[i]
                    i += 1
                else:
                    self.non_coding_seqs.append(
                        Sequence(cur_non_coding_string, i))
                    cur_non_coding_string = ''
                    i = stop

                    j += 1
                    if j < len(coding_regions_list):
                        start, stop = coding_regions_list[j]
                    else:
                        self.non_coding_seqs.append(
                            Sequence(''.join(working_seq[i:]), i))
                        break

    def translate_non_coding_seqs(self):
        '''
        Iterates through the non coding sequences stored in non_coding_seqs
        and calls translation_siz_shooter to translate the nucleotide
        sequence into all six reading frames.
        '''
        for ncs in self.non_coding_seqs:
            ncs.translation_six_shooter()

    def write_peptides_to_fasta_file(self, output_dir, stop_codon_symbol='*', min_len=6):
        '''
        DRAFT
        After the noncoding peptides have been translated this function is
        called to write those peptides to a file so a motif finding or
        clustering program can find conserved and or differential sequences.
        Currently the headers for each peptide are pretty minimal and will be
        reworked to include more info soon.

        :param: output_dir: String. Path to directory where fasta file will be written
        :param: stop_codon_symbol: Char. Symbol used for stop codon in translated seqs. Default = '*'
        :param: min_len: Int. Minimum length required for peptide to be written.
        '''
        file_basename = '{}_peptides'.format(
            os.path.basename(self.genome_file))
        file_path = os.path.join(output_dir, file_basename)
        with open(file_path, 'w') as fp:
            for noncoding_seq in self.non_coding_seqs:
                # get noncoding seq objects
                for i, frame in enumerate(noncoding_seq.frames):
                    # get individual reading fram
                    peptides = str(frame).split(stop_codon_symbol)
                    for j, pep in enumerate(peptides):
                        if len(pep) >= min_len:
                            fp.write('>frame {} seq {}\n'.format(i, j))
                            fp.write(pep + '\n')
                    # write the individual peptides

    # read in the genome file
    # get positions of coding regions
    # extract the non-coding regions and write to a file
