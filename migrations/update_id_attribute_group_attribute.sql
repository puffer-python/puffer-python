alter table attribute_group_attribute
	add not exists id int first;

set @row:=0;

update attribute_group_attribute set id = (@row:=@row+1);

alter table attribute_group_attribute drop exists key attribute_group_id;

alter table attribute_group_attribute
	add constraint attribute_group_attribute_pk
		primary key (id);



alter table attribute_group_attribute modify id int auto_increment;
