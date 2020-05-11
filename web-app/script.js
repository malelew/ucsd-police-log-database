fillTable = function(data) {
  if(data){
    var i = 0;
    var len = data.length;
    var tableContent = "";
    var headers = "";

    if(len > 0){
      keys = Object.keys(data[0]);
      console.log(keys);

      for(var i=0;i<keys.length;i++){
        headers += "<th>"+keys[i]+"</th>";
      }

      for(i=0;i<data.length;i++){
        console.log(i);
        row = "";
        for(var j=0;j<keys.length;j++){
          row += "<td>"+data[i][keys[j]]+"</td>";
        }
        tableContent += "<tr>"+row+"</tr>";
      }

      console.log(headers);
      $("#police-data-table-head-tr").append(headers);
      $("#police-data-table").append(tableContent).removeClass("hidden");
    }
  }
},

$(document).ready( function () {
  console.log('integrated');
  console.log(police_data[0]);
  fillTable(police_data);
  var table = $('#police-data-table').DataTable();
} );
