import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
from typing import List, IO
from io import StringIO

class SpatialMassFingerprinter:
    """
    A class to perform spatial mass fingerprinting by matching peaks from a
    MALDI peak list to peptide-spectrum matches (PSMs) from a DDA experiment.
    """
    def __init__(self):
        """
        Initializes the SpatialMassFingerprinter class.
        """
        self.peak_df = None
        self.psm_df = None
        self.filtered_psm_df = None
        self.results_df = pd.DataFrame()
        self.ppm_tolerance = 10
        self.hyperscore_threshold = 18.0
        self.charge_states = [1]
        self.logger = None # Placeholder for a logger object

    def set_logger(self, logger):
        """Assigns a logger object to stream messages to the UI."""
        self.logger = logger

    def _log(self, message: str):
        """Logs a message to the provided logger if it exists."""
        if self.logger:
            self.logger.push(message)
        else:
            print(message) # Fallback to console print

    def load_data_from_stream(self, peak_file_stream: IO, psm_file_stream: IO, psm_file_name: str):
        """Loads data from in-memory file streams."""
        try:
            self._log("Loading peak list...")
            self.peak_df = pd.read_csv(peak_file_stream)
            self._log(f"-> Successfully loaded peak list. Shape: {self.peak_df.shape}")

            self._log("Loading PSM data...")
            _, psm_ext = os.path.splitext(psm_file_name)
            separator = '\t' if psm_ext.lower() in ['.tsv', '.txt'] else ','
            self._log(f"-> Detected '{psm_ext}' extension, using '{separator}' as separator.")
            
            psm_content = psm_file_stream.read().decode('utf-8')
            self.psm_df = pd.read_csv(StringIO(psm_content), sep=separator)
            self._log(f"-> Successfully loaded PSM data. Shape: {self.psm_df.shape}")
            
            return True
        except Exception as e:
            self._log(f"ERROR: Failed to load data. Details: {e}")
            raise

    def set_parameters(self, ppm_tolerance: int, hyperscore_threshold: float, charge_states: List[int]):
        """Sets the analysis parameters."""
        self.ppm_tolerance = ppm_tolerance
        self.hyperscore_threshold = hyperscore_threshold
        self.charge_states = charge_states
        self._log("Parameters updated:")
        self._log(f"  - PPM Tolerance: {self.ppm_tolerance}")
        self._log(f"  - Hyperscore Threshold: {self.hyperscore_threshold}")
        self._log(f"  - Charge States: {self.charge_states}")

    def _filter_psms(self):
        """(Private) Filters PSMs based on set criteria."""
        if self.psm_df is None: return
        self._log("Filtering PSMs...")
        initial_count = len(self.psm_df)
        
        self.filtered_psm_df = self.psm_df[
            (self.psm_df['Hyperscore'] > self.hyperscore_threshold) &
            (self.psm_df['Charge'].isin(self.charge_states))
        ].copy()
        
        filtered_count = len(self.filtered_psm_df)
        self._log(f"-> Initial PSM count: {initial_count}")
        self._log(f"-> PSMs after filtering: {filtered_count}")

    def perform_fingerprinting(self, psm_column_to_use: str = 'Calibrated Observed Mass'):
        """Performs the core peak-to-peptide matching."""
        if self.peak_df is None or self.psm_df is None:
            self._log("ERROR: Data not loaded. Cannot perform fingerprinting.")
            return pd.DataFrame()

        self._log("\nStarting mass fingerprinting...")
        self._filter_psms()

        if self.filtered_psm_df is None or self.filtered_psm_df.empty:
            self._log("Warning: No PSMs remained after filtering. Cannot perform matching.")
            self.results_df = pd.DataFrame()
            return self.results_df

        self._log("Matching peaks to filtered peptides...")
        all_matches = []
        total_peaks = len(self.peak_df)
        for i, (_, peak_row) in enumerate(self.peak_df.iterrows()):
            if (i + 1) % 100 == 0:
                self._log(f"  - Processing peak {i+1}/{total_peaks}...")
            
            peak_mz = peak_row['m/z']
            tolerance_da = (self.ppm_tolerance / 1e6) * peak_mz
            mass_lower_bound, mass_upper_bound = peak_mz - tolerance_da, peak_mz + tolerance_da
            
            matches_df = self.filtered_psm_df[
                self.filtered_psm_df[psm_column_to_use].between(mass_lower_bound, mass_upper_bound)
            ].copy()

            if not matches_df.empty:
                matches_df['MALDI M/Z Value'] = peak_mz
                matches_df['Mass Error (ppm)'] = ((matches_df[psm_column_to_use] - peak_mz) / peak_mz) * 1e6
                all_matches.extend(matches_df.to_dict('records'))

        self.results_df = pd.DataFrame(all_matches)
        if not self.results_df.empty:
            self.results_df.set_index('MALDI M/Z Value', inplace=True)
        
        self._log(f"Fingerprinting complete. Found {len(self.results_df)} total matches.")
        return self.results_df
    
    def get_results(self) -> pd.DataFrame:
        """Returns the results dataframe."""
        return self.results_df

    def plot_mass_error_distribution(self, bins: int = 50):
        """Generates a histogram of mass error distribution."""
        fig, ax = plt.subplots(figsize=(10, 6))
        if not self.results_df.empty:
            sns.histplot(self.results_df['Mass Error (ppm)'], bins=bins, kde=True, ax=ax)
            ax.axvline(0, color='red', linestyle='--', linewidth=1.5)
        ax.set_title('Mass Error Distribution', fontsize=16)
        ax.set_xlabel('Mass Error (ppm)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        plt.tight_layout()
        return fig

    def plot_hyperscore_vs_mass_error(self):
        """Generates a scatter plot of Hyperscore vs. Mass Error."""
        fig, ax = plt.subplots(figsize=(10, 6))
        if not self.results_df.empty:
            sns.scatterplot(data=self.results_df, x='Mass Error (ppm)', y='Hyperscore', alpha=0.7, ax=ax)
        ax.set_title('Hyperscore vs. Mass Error', fontsize=16)
        ax.set_xlabel('Mass Error (ppm)', fontsize=12)
        ax.set_ylabel('Hyperscore', fontsize=12)
        plt.tight_layout()
        return fig

    def plot_hits_per_mass_bin(self, bin_width: int = 10):
        """Generates a histogram of peptide hits per mass bin."""
        fig, ax = plt.subplots(figsize=(12, 7))
        if not self.results_df.empty:
            mass_values = self.results_df.index
            min_mass = int(mass_values.min() // bin_width * bin_width)
            max_mass = int(mass_values.max() // bin_width * bin_width) + bin_width
            bins = np.arange(min_mass, max_mass + bin_width, bin_width)
            sns.histplot(x=mass_values, bins=bins, ax=ax)
        ax.set_title(f'Peptide Identifications per {bin_width} Da Bin', fontsize=16)
        ax.set_xlabel('m/z', fontsize=12)
        ax.set_ylabel('Number of Matched Peptides', fontsize=12)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
