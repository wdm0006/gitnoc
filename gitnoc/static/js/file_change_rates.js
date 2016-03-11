$(document).ready(function() {
    $('#file_change_rates_table').DataTable( {
        "ajax": '/file_change_rates',
        "scrollX": true
    });
} );