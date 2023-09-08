# 1. First steps in R:# 
## 1.1 - We start by cleaning R environment ##
##install.packages("readxl")
##install.packages("remotes")
##install.packages("RSQLite")
##install.packages("dplyr")
#install.packages("gstat")
install.packages("brewer")
install.packages("RColorBrewer")


library(RSQLite)           # Carrega o pacote RSQLite
library(readxl)
library(dplyr)
library(remotes)
#install_github("r-spatial/sf")
library(sf)
library(gstat)
library(brewer)
library(RColorBrewer)


rm(list = ls())
gc(reset=T)
graphics.off()
data_med = '2022-05-24'

#install.packages("RSQLite")  # Instala o pacote RSQLite, se ainda não estiver instalado
#library(RSQLite)           # Carrega o pacote RSQLite

## 1.2 - And install required packages

pacman::p_load(gstat, raster, rstudioapi, sp, sf, spacetime, rgdal, RColorBrewer)

## 1.3 - Than we set working directory to source file location (directory turns to be the location where the R script is saved in your computer)

## 1.4 - Loading data: our data is already free of outliers; we strongly recommend data preprocessing prior to interpolation


data = estacoes_mp10 <- read_xlsx("/home/caue/Documentos/pensi_projeto/datasaude-scripts/R/geolocalizacao_estacoes_lat_long.xlsx")

# Carregar dados
con <- dbConnect(SQLite(), dbname = "/home/caue/Documentos/pensi_projeto/datasaude-scripts/R/db1.sqlite")
poluente_media <- dbGetQuery(con, "SELECT * FROM poluente_historico")%>% mutate(data_medicao = as.Date(data))
tabelas <- dbListTables(con)
dbDisconnect(con)

pol.dias <- poluente_media %>% group_by(nome_parametro, data_medicao)%>%
  summarise(media_dia=mean(media_horaria),
            .groups = 'drop')

mp10 <- poluente_media %>%filter(nome_parametro=='MP10 (Partículas Inaláveis)',
                                 data_medicao== data_med)%>% left_join(estacoes_mp10)%>%
  group_by(lat_UTM, long_UTM, nome_estacao)%>%
  summarise(media_dia=mean(media_horaria),
            .groups = 'drop')


data <- mp10[,c(1,2,4)] #selecting important columns (x, y, z)
data$lat_UTM <- as.numeric(data$lat_UTM)
data$long_UTM <- as.numeric(data$long_UTM)
names(data) <- c("x", "y", "z")

sp::coordinates(data) = ~x+y # transform data to spatial object (x and y must be in UTM)


## 1.5 - We separate the primary variable. This will facilitate analysis

mp10_atr<- data$z


## 1.6 - Data visualization according to the "z" values

sp::bubble(data, "z", col = "red")

# 2. k-fold cross validation.

## 4.1 - We create a grid for interpolation

contorno <- shapefile("/home/caue/Documentos/pensi_projeto/QGIS/Interpolação/contorno_sha.shp")

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
            filename = '/home/caue/Documentos/pensi_projeto/datasaude-scripts/R/interpolated_idw.tif',#here we choose where we want to save
            format = 'GTiff',
            overwrite = T)

###IDW
###Inverso da distancia
par(mar = c(1, 1, 1, 1))
pontos <- st_as_sf(mp10, coords = c("long_UTM", "lat_UTM"), crs = 31983)
modelo_raster <- raster('/home/caue/Documentos/pensi_projeto/datasaude-scripts/R/interpolated_idw.tif', values = FALSE)
st_crs(pontos) <- crs(modelo_raster)
sp <- st_read("/home/caue/Documentos/pensi_projeto/datasaude-scripts/R/UTM_Limites_RMSP/UTM_Limites_RMSP.shp")
st_crs(sp) <- 31983
gs_idw_2 <- gstat(formula = media_dia~1, locations = pontos, set = list(idp=3))
interpolacao_idw <- interpolate(modelo_raster, gs_idw_2)
num_intervals <- 10
interval_colors <- brewer.pal(num_intervals, "Oranges")
plot(interpolacao_idw, col = interval_colors, col.regions = interval_colors, main = data_med)
plot(st_geometry(sp), add = TRUE)



