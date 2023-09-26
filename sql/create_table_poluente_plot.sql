CREATE TABLE poluente_plot (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	data_coleta TEXT(20),
	poluente TEXT(10),
	vmin NUMERIC,
	vmax NUMERIC,
	escala TEXT,
	arquivo_geojson INTEGER,
	arquivo_png INTEGER,
	data_atual DATE,
	status TEXT(20)
);
CREATE UNIQUE INDEX poluente_plot_data_coleta_IDX ON poluente_plot (data_coleta,poluente,vmin,vmax);
