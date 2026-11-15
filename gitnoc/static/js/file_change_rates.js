$(document).ready(function() {
    $('#file_change_rates_table').DataTable( {
        "ajax": '/file_change_rates',
        "scrollX": true,
        "columnDefs": [
            { "targets": [0, 1], "className": "mono" },
            { "targets": [2, 3, 4, 5, 6], "className": "num" }
        ]
    });
} );
