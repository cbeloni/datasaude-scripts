# 1. First steps in R:# 
## 1.1 - We start by cleaning R environment ##
rm(list = ls())
gc(reset=T)
graphics.off()
data_med = '2022-05-24'

#install.packages("RSQLite")  # Instala o pacote RSQLite, se ainda não estiver instalado
library(RSQLite)           # Carrega o pacote RSQLite

## 1.2 - And install required packages

pacman::p_load(gstat, raster, rstudioapi, sp, sf, spacetime, rgdal, RColorBrewer)

## 1.3 - Than we set working directory to source file location (directory turns to be the location where the R script is saved in your computer)

## 1.4 - Loading data: our data is already free of outliers; we strongly recommend data preprocessing prior to interpolation

data = estacoes_mp10 <- read_xlsx("geolocalizacao_estacoes_lat_long.xlsx")

# Carregar dados
con <- dbConnect(SQLite(), dbname = "db1.sqlite")
poluente_media <- dbGetQuery(con, "SELECT * FROM poluente_historico")%>% mutate(data_medicao = as.Date(data))
tabelas <- dbListTables(con)
dbDisconnect(con)

mp10 <- poluente_media %>%filter(nome_parametro=='MP10 (Partículas Inaláveis)',
                                 data_medicao== data_med)%>% left_join(estacoes_mp10)%>%
  group_by(lat_UTM, long_UTM, nome_estacao)%>%
  summarise(media_dia=mean(media_horaria),
            .groups = 'drop')


data <- mp10[,c(1,2,4)] #selecting important columns (x, y, z)

names(data) <- c("x", "y", "z")

sp::coordinates(data) = ~x+y # transform data to spatial object (x and y must be in UTM)


## 1.5 - We separate the primary variable. This will facilitate analysis

mp10_atr<- data$z


## 1.6 - Data visualization according to the "z" values

sp::bubble(data, "z", col = "red")

# 2. k-fold cross validation.

## 4.1 - We create a grid for interpolation

contorno <- shapefile("Mun_RMSP_UTM.shp")

#And then we create a grid

r = raster::raster(contorno, res = 1000) #  "res" sets pixel resolution

rp = raster::rasterize(contorno, r, 0) 

grid = as(rp, "SpatialPixelsDataFrame") 

sp::plot(grid)

sp::proj4string(data) = CRS(proj4string(grid)) # Contorno (shape) and data have the same CRS

##4.1 - Convert to raster

mapaRaster = raster(mapa)

proj4string(mapaRaster) = proj4string(contorno) 

## 4.2 - Exporting the map

writeRaster(mapaRaster, 
            filename = 'interpolated_idw.tif',#here we choose where we want to save
            format = 'GTiff',
            overwrite = T)

###IDW
###Inverso da distancia
pontos <- st_as_sf(mp10, coords = c("long_UTM", "lat_UTM"), crs = 31983)
st_crs(pontos) <- crs(modelo_raster)
gs_idw_2 <- gstat(formula = media_dia~1, locations = pontos, set = list(idp=3))
interpolacao_idw <- interpolate(modelo_raster, gs_idw_2)
num_intervals <- 10
interval_colors <- brewer.pal(num_intervals, "Oranges")
plot(interpolacao_idw, col = interval_colors, col.regions = interval_colors, main = data_med)
plot(st_geometry(sp), add = TRUE)



cv_idw_2<-gstat.cv(gs_idw_2)
resultados<-(as.data.frame(cv_idw_2))
sqrt(mean(cv_idw_2$residual^2))
1-(var(cv_idw_2$residual)/var(cv_idw_2$observed))

modelo_raster <- raster('interpolated_idw.tif', values = FALSE)
st_crs(pontos) <- crs(modelo_raster)

interpolacao_idw <- interpolate(modelo_raster, gs_idw_2)


gs_idw_2$data

num_intervals <- 10
interval_colors <- brewer.pal(num_intervals, "Oranges")
plot(interpolacao_idw, col = interval_colors, col.regions = interval_colors, main = data_med)
plot(st_geometry(sp), add = TRUE)

interpolacao_idw@data
teste@data



sp <- st_read("Mun_RMSP_UTM.shp")
st_crs(sp) <- 31983


plot(teste)
plot(st(geometry(modelo_raster), add = TRUE))
plot(teste, main = "MP10 - Data: 2022-12-25")
plot(st_geometry(sp), add = TRUE)

num_intervals <- 10
interval_colors <- brewer.pal(num_intervals, "Oranges")
plot(teste, col = interval_colors, col.regions = interval_colors, main = "MP10 - Data: 2022-12-25")
plot(st_geometry(sp), add = TRUE)


display.brewer.all()


plot(sp)
sp <- st_read("Mun_RMSP_UTM.shp")
st_crs(sp) <- 31983


estacoes <- st_read(mp10)
tm_shape(pontos) + tm_dots(col = 'media_dia', pal = "red")+
  tm_shape(contorno) + tm_borders(col = 'black')



pontos <- st_as_sf(mp10, coords = c("long_UTM", "lat_UTM"), crs = 31983)

estacoes_1 <- st_as_sf(sp, coords = c("long_UTM", "lat_UTM"), crs = 31983)

plot(mp10)

proj4string(modelo_raster)
proj4string(pontos)


library('fields')
modelo_tps <- Tps(x=st_coordinates(pontos), Y=pontos$media_dia)
sqrt(mean(modelo_tps$residuals^2))
1-(var(modelo_tps$residuals)/var(pontos$media_dia))
modelo_tps$fitted.values
mp10_spline <- interpolate(modelo_raster, modelo_tps)
plot(mp10_spline)
plot(st_geometry(sp), add = TRUE)


# CONVERTER UM DATA FRAME EM SHAPEFILE
meu_sf <- st_as_sf(mp10, coords = c("long_UTM", "lat_UTM"), crs = 31983)
write_sf(meu_sf, file.path(caminho_do_arquivo, "nome_do_shapefile.shp"))

