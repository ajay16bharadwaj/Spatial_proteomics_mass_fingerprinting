from nicegui import ui
from io import BytesIO
import traceback
import base64
import matplotlib.pyplot as plt

# Import the class from the other file
from spatial_mass_fingerprinter import SpatialMassFingerprinter

# --- NiceGUI Application ---

# Create an instance of our fingerprinter
fingerprinter = SpatialMassFingerprinter()

# Dictionary to hold uploaded file data
uploaded_files = {
    "peak_list": None,
    "psm_data": None,
    "psm_name": None,
}

def handle_peak_upload(e):
    """Callback for peak list file upload."""
    uploaded_files["peak_list"] = BytesIO(e.content.read())
    peak_upload_label.text = f"Uploaded: {e.name}"
    ui.notify(f"Peak list '{e.name}' uploaded.", color='positive')

def handle_psm_upload(e):
    """Callback for PSM data file upload."""
    uploaded_files["psm_data"] = BytesIO(e.content.read())
    uploaded_files["psm_name"] = e.name # Store filename to check extension
    psm_upload_label.text = f"Uploaded: {e.name}"
    ui.notify(f"PSM data '{e.name}' uploaded.", color='positive')

async def run_analysis():
    """The main function to trigger the analysis."""
    if not uploaded_files["peak_list"] or not uploaded_files["psm_data"]:
        ui.notify("Please upload both peak list and PSM data files.", color='negative')
        return

    # Clear previous results and logs
    log.clear()
    results_table.clear()
    plot_area_1.clear()
    plot_area_2.clear()
    plot_area_3.clear()
    download_button.visible = False
    filter_input.visible = False
    filter_input.value = ''


    try:
        # Reset file stream pointers to the beginning
        uploaded_files["peak_list"].seek(0)
        uploaded_files["psm_data"].seek(0)

        # Parse charge states from string input "1, 2, 3" to list [1, 2, 3]
        charge_states_list = [int(c.strip()) for c in charge_states_input.value.split(',')]
        
        # Assign the UI log to the fingerprinter instance
        fingerprinter.set_logger(log)
        
        # Use a spinner to indicate that the app is busy
        with ui.spinner(size='lg', color='primary'):
            # Load data
            fingerprinter.load_data_from_stream(
                peak_file_stream=uploaded_files["peak_list"],
                psm_file_stream=uploaded_files["psm_data"],
                psm_file_name=uploaded_files["psm_name"]
            )

            # Set parameters
            fingerprinter.set_parameters(
                ppm_tolerance=ppm_input.value,
                hyperscore_threshold=hyperscore_input.value,
                charge_states=charge_states_list
            )
            
            # Run the main analysis
            results_df = fingerprinter.perform_fingerprinting()

        # Display results table
        if not results_df.empty:
            table_df = results_df.reset_index()
            cols = [{'name': col, 'label': col, 'field': col, 'sortable': True} for col in table_df.columns]
            with results_table:
                # Create the table with pagination and bind the filter
                table = ui.table(columns=cols, rows=table_df.to_dict('records'), row_key='Peptide', pagination=25).classes('w-full')
                table.bind_filter_from(filter_input, 'value')
            
            download_button.visible = True
            filter_input.visible = True # Show the search bar

        # Generate and display plots
        log.push("Generating visualizations...")
        
        # Correctly display plots by converting them to base64 images
        with plot_area_1:
            fig = fingerprinter.plot_mass_error_distribution()
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)  # Close the figure to free up memory
            b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            ui.image(f'data:image/png;base64,{b64_str}')

        with plot_area_2:
            fig = fingerprinter.plot_hyperscore_vs_mass_error()
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            ui.image(f'data:image/png;base64,{b64_str}')

        with plot_area_3:
            fig = fingerprinter.plot_hits_per_mass_bin()
            buf = BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight')
            plt.close(fig)
            b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
            ui.image(f'data:image/png;base64,{b64_str}')

        log.push("Done.")
        ui.notify("Analysis finished successfully!", color='positive')

    except Exception as e:
        # Catch any exception during the process and log it
        tb = traceback.format_exc()
        log.push(f"--- ANALYSIS FAILED ---\n{tb}")
        ui.notify(f"An error occurred: {e}", color='negative', multi_line=True)


@ui.page('/')
def main_page():
    """Defines the UI layout and elements."""
    global peak_upload_label, psm_upload_label, ppm_input, hyperscore_input, charge_states_input
    global results_table, download_button, plot_area_1, plot_area_2, plot_area_3, log, filter_input
    
    ui.add_head_html('<style>body {background-color: #f4f4f8;}</style>')
    
    with ui.header().classes('bg-primary text-white shadow-md'):
        ui.label('Spatial Mass Fingerprinting').classes('text-2xl font-bold')

    with ui.card().classes('w-full max-w-4xl mx-auto mt-6'):
        ui.label('1. Upload Data Files').classes('text-xl font-semibold')
        with ui.row().classes('w-full items-center'):
            ui.upload(on_upload=handle_peak_upload, auto_upload=True).props('accept=".csv"').classes('flex-1')
            peak_upload_label = ui.label('Upload Peak List (.csv)').classes('ml-4')
        with ui.row().classes('w-full items-center mt-2'):
            ui.upload(on_upload=handle_psm_upload, auto_upload=True).props('accept=".tsv,.csv,.txt"').classes('flex-1')
            psm_upload_label = ui.label('Upload PSM Data (.tsv, .csv, .txt)').classes('ml-4')
    
    with ui.card().classes('w-full max-w-4xl mx-auto mt-6'):
        ui.label('2. Set Parameters').classes('text-xl font-semibold')
        with ui.row().classes('w-full items-center gap-4'):
            ppm_input = ui.number(label='PPM Tolerance', value=10, min=1, step=1).classes('w-32')
            hyperscore_input = ui.number(label='Hyperscore Threshold', value=18.0, step=0.1).classes('w-32')
            charge_states_input = ui.input(label='Charge States (comma-separated)', value='1,2').classes('flex-1')

    with ui.card().classes('w-full max-w-4xl mx-auto mt-6'):
        ui.button('Run Analysis', on_click=run_analysis, icon='science').props('color=primary size=lg')

    with ui.card().classes('w-full max-w-4xl mx-auto mt-6'):
        ui.label('Log').classes('text-xl font-semibold')
        log = ui.log().classes('w-full h-40 bg-gray-100 p-2 rounded')

    with ui.card().classes('w--full max-w-4xl mx-auto mt-6'):
        with ui.row().classes('w-full justify-between items-center'):
            ui.label('3. Results').classes('text-xl font-semibold')
            download_button = ui.button('Download CSV', on_click=lambda: ui.download(get_csv(), 'fingerprinting_results.csv'), icon='download').props('color=secondary')
            download_button.visible = False
        
        # Input for filtering the table
        filter_input = ui.input(placeholder='Search results...').props('dense clearable').classes('w-full mb-2')
        filter_input.visible = False
        
        results_table = ui.column().classes('w-full')

    with ui.card().classes('w-full max-w-4xl mx-auto mt-6'):
        ui.label('4. Visualizations').classes('text-xl font-semibold')
        plot_area_1 = ui.column().classes('w-full border rounded p-2 mt-2')
        plot_area_2 = ui.column().classes('w-full border rounded p-2 mt-4')
        plot_area_3 = ui.column().classes('w-full border rounded p-2 mt-4')

def get_csv():
    """Function to generate the CSV content for download."""
    df_to_download = fingerprinter.get_results().reset_index()
    return df_to_download.to_csv(index=False).encode()

# Run the app
ui.run()
