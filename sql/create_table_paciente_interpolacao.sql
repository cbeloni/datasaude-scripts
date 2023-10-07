create table paciente_interpolacao
(
    id  int not null,
    id_coordenada int not null,
    data          varchar(50),
    MP10          varchar(50),
    NO          varchar(50),
    NO2          varchar(50),
    O3          varchar(50),
    TEMP          varchar(50),
    UR          varchar(50)
);

alter table paciente_interpolacao
    add constraint paciente_interpolacao_pk
        primary key (id);

alter table paciente_interpolacao
    add constraint paciente_interpolacao_paciente_coordenadas_id_fk
        foreign key (id_coordenada) references paciente_coordenadas (id);

alter table paciente_interpolacao
    modify id int auto_increment;

alter table paciente_interpolacao
    auto_increment = 1;

