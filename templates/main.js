document.getElementById("updateButton").addEventListener("click", function () {
        // Send an AJAX request to update_table endpoint
        fetch("/_chickDesc", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
        })
        .then(response => response.json())
        .then(data => {
            $("table tr").remove();
            // Update the table with the new data
            var table = document.getElementById("table");
            table.innerHTML = `
                <tr>
                    <th>ID</th>
                    <th>CATEGORIA</th>
                    <th>PRECISION</th>
                </tr>
            `;
            data.forEach(entry => {
                table.innerHTML += `
                    <tr>
                        <td>${entry.ID}</td>
                        <td>${entry.CATEGORIA}</td>
                        <td>${entry.PRECISION}</td>
                    </tr>
                `;
            });
        })
        .catch(error => console.error("Error:", error));
      });
      document.getElementById("updateButton1").addEventListener("click", function () {
        // Send an AJAX request to update_table endpoint
        fetch("/_chickCount", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({}),
        })
        .then(response => response.json())
        .then(dataCount => {
          $("tableCount tr").remove();
            // Update the table with the new data
            var table1 = document.getElementById("tableCount");
            table1.innerHTML = `
                <tr>
                    <th>Pollos vivos</th>
                    <th>Pollos muertos</th>
                </tr>
            `;
            dataCount.forEach(entry => {
                table1.innerHTML += `
                    <tr>
                        <td>${entry.PMuerto}</td>
                        <td>${entry.PVivo}</td>
                    </tr>
                `;
            });
        })
        .catch(error => console.error("Error:", error));
      });