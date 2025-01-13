from langchain_community.utilities.sql_database import SQLDatabase
import pandas as pd
import streamlit as st
import SQLUtility
import PlotGraph as pg
import datetime
import json

mapping_gui_template=r"MATCH(N:{0}) WHERE N.TRAN_AMT={1} and N.TRAN_ACCT='{2}' AND N.TRAN_DT='{3}' RETURN N"	

mapping_template_expanded=r="MATCH (A:{0})<-[:EXTRACTED_FROM_precsa]-(B:PRECSA)  <-[:EXTRACTED_FROM_stitch]-(C:STITCH)\
MATCH (C:STITCH)<-[:EXTRACTED_FROM_kde1]-(D:KDE1)<-[:EXTRACTED_FROM_Src1Stg1]-(F:SRC1_STG)<-[:EXTRACTED_FROM_Src1File1]-(I:SRC1_FILE)\
MATCH (C:STITCH)<-[:EXTRACTED_FROM_kde2]-(E:KDE2)<-[:EXTRACTED_FROM_Src2Stg1]-(G:SRC2_STG1)<-[:EXTRACTED_FROM_Src2File1]-(J:SRC2_FILE1)\
MATCH (C:STITCH)<-[:EXTRACTED_FROM_kde2]-(E:KDE2)<-[:EXTRACTED_FROM_Src2Stg2]-(H:SRC2_STG2)<-[:EXTRACTED_FROM_Src2File2]-(K:SRC2_FILE2)\
WHERE  A.TRAN_AMT={1}  and A.TRAN_ACCT='{2}' AND A.TRAN_DT='{3}' \
RETURN A, B,C,D,E,F,G,H,I,J,K" 

stg_src1_query='SELECT "TRAN_DESC", "ORIGNTR_ACCT_ID" \
    from	"TD_DEMO_SCHEMA"."STG_SRC1_STITCHED" \
where  "TRAN_AMT" = cast(:tranamt as varchar(20)) 	'''


#
query='SELECT txn_ref_no, fic_mis_date, account_number, txn_value_date, drcr_indicator, txn_desc,\
tran_prod_type_cd_tmp, txn_amt, txn_amt_acy	\
	FROM "DEMO2"."FIN_ACCT_TXNS"\
	where txn_ref_no= cast(:txn_ref_no as varchar(50))'

#PRE-CSA TO CSA FIN_ACCT_TXNS:
#############################

precsa_csa= 'SELECT  txn_ref_no, fic_mis_date, account_number, txn_value_date, drcr_indicator,\
txn_desc, tran_prod_type_cd_tmp, txn_amt, txn_amt_acy\
	FROM "DEMO2"."FIN_ACCT_TXNS"\
	where txn_ref_no=cast(:txn_ref_no as varchar(50))\
	UNION \
SELECT txn_ref_no, fic_mis_date, account_number, txn_value_date, drcr_indicator, txn_desc,\
tran_prod_type_cd_tmp, txn_amt, txn_amt_acy\
	FROM "DEMO2"."PRE_FIN_ACC_TXNS"\
	where txn_ref_no=cast(:txn_ref_no as varchar(50))'




#STITCH TO PRE-CSA;
###################

stitch_to_precsa_query=	'''SELECT  txn_ref_no, fic_mis_date, account_number, txn_value_date, drcr_indicator, txn_desc, 
tran_prod_type_cd_tmp, txn_amt, txn_amt_acy
	FROM "DEMO2"."PRE_FIN_ACC_TXNS"
	where txn_ref_no=cast(:txn_ref_no as varchar(50))
	UNION 
	select * from ( 
SELECT tran_ref_no, dl_as_of_dt as fic_mis_date, 
	case when drcr_in='C' then bnf_acct_id else origintr_acct_id end as 
	account_number, tran_val_dt, drcr_in, tran_desc, tran_prod_type_cd_tmp, txn_amt, tran_amnt_act_cur 
    FROM 	( 
	SELECT bnf_acct_id, drcr_in, tran_val_dt, origintr_acct_id, tran_desc, tran_prod_type_cd_tmp, 
          	tran_ref_no, orig_dl_as_of_dt, dl_as_of_dt, dl_source_cd, txn_amt, tran_grp_cd_tmp, stitch_flag, 
     tran_acct1_tmp, tran_amt_tmp, tran_dt_tmp, tran_type_cd_tmp,
	tran_amnt_act_cur 
	FROM "DEMO2"."SRC1_STITCHED"
) TMP)
	where  tran_ref_no=cast(:txn_ref_no as varchar(50))'''

GET_ADDITIONAL_PARAMS='SELECT  txn_ref_no, account_number, txn_value_date,  txn_amt\
	FROM "DEMO2"."PRE_FIN_ACC_TXNS"\
	where txn_ref_no=cast(:txn_ref_no as varchar(50))'
 
 
GET_NACHA_PARAMS='''WITH SRC2_STG1_CTE AS (
SELECT 'SRC2_STG1' as mapping, nacha_050_coll_file_no, nacha_5, dl_as_of_dt, dl_source_cd, nacha_050_coll_btch_no, ifw_eff_dt, nacha_050_coll_pt
	FROM "DEMO2"."SRC2_STG1"
),
SRC2_STG2_CTE AS (	
SELECT 'SRC2_STG2' as mapping,nacha_060_coll_file_no,nacha_6, dl_as_of_dt, dl_source_cd, nacha_060_dtl_par, nacha_060_coll_btch_no, ifw_eff_dt, nacha_060_coll_pt
	FROM "DEMO2"."SRC2_STG2"
),
JOINS_SRC_CTES AS ( select b.*,a.* from SRC2_STG1_CTE a 
	join  SRC2_STG2_CTE b
	on a.nacha_050_coll_file_no=b.nacha_060_coll_file_no
	and a.nacha_050_coll_btch_no=b.nacha_060_coll_btch_no
	)
 
select nacha_050_coll_file_no,nacha_050_coll_btch_no from(
Select
nacha_050_coll_file_no,nacha_050_coll_btch_no,
cast(cast(substr(nacha_6, 30, 10) as int)/100.0 as numeric(18,2)) as tran_amt_tmp,
to_date(substr(nacha_5,70,6),'yyMMdd') as tran_dt_tmp
from JOINS_SRC_CTES )
	where tran_amt_tmp=:tranamnt
	and cast(tran_dt_tmp as date)=cast(:trandate as date)
 '''

#KDE to Stitch

KDE_To_Stitch_query='''WITH KDE1_CTE AS(
	SELECT tran_amnt, bnf_acct_id, drcr_in, tran_val_dt, origntr_acct_id, tran_desc, tran_ref_no, tran_prod_type_cd_tmp, tran_acct1_tmp, tran_amt_tmp, tran_dt_tmp, tran_type_cd_tmp, dl_as_of_dt, dl_source_cd, bnf_acct_id_type, origntr_acct_id_type, acc_ident, tran_amnt_act_cur
	FROM "DEMO2"."SRC1_KDE"
)
	,
KDE2_CTE AS(
SELECT drcr_in, origntr_acct_id, tran_acct1_tmp, tran_amt_tmp, tran_dt_tmp, dl_as_of_dt, dl_source_cd, txn_amt, acc_ident_nbr
FROM "DEMO2"."SRC2_KDE"
)
,
	KDE_JOINS AS
	(
	SELECT KDE1.tran_desc, 
	CASE WHEN KDE1.drcr_in ='D' THEN KDE1.origntr_acct_id ELSE KDE2.origntr_acct_id END AS origntr_acct_id,
	CASE WHEN KDE1.drcr_in ='C' THEN KDE1.bnf_acct_id ELSE NULL END AS bnf_acct_id,
	KDE1.tran_prod_type_cd_tmp  tran_prod_type_cd_tmp,
	KDE1.drcr_in AS drcr_in
	, KDE1.tran_amnt AS tran_amnt
	, KDE1.tran_val_dt AS tran_val_dt
	, KDE1.tran_acct1_tmp AS tran_acct1_tmp  
	,KDE1.tran_ref_no

	
	FROM
	"DEMO2"."SRC1_KDE" KDE1 JOIN "DEMO2"."SRC2_KDE" KDE2
	ON KDE1.tran_acct1_tmp = KDE2.tran_acct1_tmp AND
	KDE1.tran_amt_tmp = KDE2.tran_amt_tmp AND
	KDE1.tran_dt_tmp = KDE2.tran_dt_tmp 
	)  
	SELECT 'KDE1-2' as map	,	* FROM KDE_JOINS
where 
	
	tran_ref_no=cast(:txn_ref_no as varchar(50))
	
union
	
select 'STITCH' as map,tran_desc,origintr_acct_id,bnf_acct_id,tran_prod_type_cd_tmp,drcr_in,
	txn_amt,tran_val_dt,tran_acct1_tmp,tran_ref_no
	from "DEMO2"."SRC1_STITCHED"
where tran_ref_no=cast(:txn_ref_no as varchar(50))'''



#SRC1_STAGING_DATA TO STG_SRC1_KDE
#########################################
	
stg_src1_KDE_query='''SELECT 'SRC1-KDE' as mapping,tran_amnt, bnf_acct_id, drcr_in,
	to_date(tran_val_dt,'dd-mon-yy')	as tran_val_dt	, origntr_acct_id, tran_desc,
	tran_ref_no, tran_prod_type_cd_tmp, tran_acct1_tmp, tran_amt_tmp,
	to_date(tran_dt_tmp	,'dd-mon-yy')	as tran_dt_tmp	, tran_type_cd_tmp,
	to_date(	dl_as_of_dt	,'dd-mon-yy') as dl_as_of_date,
	dl_source_cd, bnf_acct_id_type, origntr_acct_id_type, acc_ident, tran_amnt_act_cur
	FROM "DEMO2"."SRC1_KDE"
	where 	tran_ref_no=cast(:txn_ref_no as varchar(50))
	UNION
	
select * from (
	select 
	
	mapping,
	tran_amnt, bnf_acct_id, drcr_in, to_date(tran_val_dt,'yyyymmdd') as tran_val_dt	, origntr_acct_id, tran_desc, 
	tran_ref_no, tran_prod_type_cd_tmp, tran_acct1_tmp, tran_amt_tmp, to_date(tran_dt_tmp,'yyyymmdd') as tran_dt_tmp	,
	tran_type_cd_tmp, dl_as_of_dt, dl_source_cd,
		case when bnf_acct_id is not null then 'IA' else null end as bnf_acct_id_type,
	case when origntr_acct_id is not null then 'IA' else null end as origntr_acct_id_type,
	acc_ident, tran_amnt_act_cur
	
	from (
select mapping, 
	case when acc_id ='1' then acc_amt
	when acc_id='3' then acc_3_amt
	when acc_id='10' then acc_10_amt
	when acc_id='09' then acc_9_amt
	when acc_id='02' then acc_2_amt
	else null end as tran_amnt,
	case 
	when acc_id='3' and acc_3_type in ('1','2','5','7') then 
	'SRC1-'||lpad(acc_3_ctl1,4,'0')||lpad(acc_3_ctl2,4,'0')||lpad(acc_3_ctl3,4,'0')||lpad(acc_3_ctl4,4,'0')||
	lpad(acc_3_acct	,10,'0')
	when acc_id='10' and acc_10_type in ('1','2','5','7') then 
	'SRC1-'||lpad(acc_10_ctl1,4,'0')||lpad(acc_10_ctl2,4,'0')||lpad(acc_10_ctl3,4,'0')||lpad(acc_10_ctl4,4,'0')||
	lpad(acc_10_acct	,10,'0')
 
	when acc_id='9' and acc_9_type in ('1','2','5','7') then 
	'SRC1-'||lpad(acc_9_ctl1,4,'0')||lpad(acc_9_ctl2,4,'0')||lpad(acc_9_ctl3,4,'0')||lpad(acc_9_ctl4,4,'0')||
	lpad(acc_9_acct	,10,'0')
 
	when acc_id='1' and acc_type in ('1','2','5','7') then 
	'SRC1-'||lpad(acc_ctl1,4,'0')||lpad(acc_ctl2,4,'0')||lpad(acc_ctl3,4,'0')||lpad(acc_ctl4,4,'0')||
	lpad(acc_acct	,10,'0')
	when acc_id='2' and acc_2_type in ('1','2','5','7') then 
	'SRC1-'||lpad(acc_2_ctl1,4,'0')||lpad(acc_2_ctl2,4,'0')||lpad(acc_2_ctl3,4,'0')||lpad(acc_2_ctl4,4,'0')||
	lpad(acc_2_acct	,10,'0')
	else
	null end  as bnf_acct_id,
	case when acc_id='3' then acc_3_type
	when acc_id='10' then acc_10_type
	when acc_id='9' then acc_9_type
	when acc_id='1' then acc_type
	when acc_id='2' then acc_2_type
end	as drcr_in,
	case when acc_id='3' then to_char(to_date(lpad(acc_ent_dt,6,'0'), 'MMDDYY'), 'YYYYMMDD') 
	when acc_id='10' then to_char(to_date(lpad(acc_ent_dt,6,'0'), 'MMDDYY'), 'YYYYMMDD')
	when acc_id='09' then to_char(to_date(lpad(acc_dt_cd ,6,'0'), 'MMDDYY'), 'YYYYMMDD')   
	when acc_id='1' then to_char(to_date(lpad(  acc_pst_dt   ,6,'0'), 'MMDDYY'), 'YYYYMMDD')   
	when acc_id='2' then NULL
	else NULL
	end as tran_val_dt,
	case 
	when acc_id='3' and acc_3_type in ('3','4','6','8') then 'SRC1-'||lpad(acc_3_ctl1,4,'0')||lpad(acc_3_ctl2,4,'0')||
	lpad(acc_3_ctl3,4,'0')||lpad(acc_3_ctl4,4,'0')||lpad(acc_3_acct,10,'0')
	when acc_id='10' and acc_3_type in ('3','4','6','8') then 'SRC1-'||lpad(acc_10_ctl1,4,'0')||lpad(acc_10_ctl2,4,'0')||
	lpad(acc_10_ctl3,4,'0')||lpad(acc_10_ctl4,4,'0')||lpad(acc_10_acct,10,'0')
	when acc_id='9' and acc_3_type in ('3','4','6','8') then 'SRC1-'||lpad(acc_9_ctl1,4,'0')||lpad(acc_9_ctl2,4,'0')||
	lpad(acc_9_ctl3,4,'0')||lpad(acc_9_ctl4,4,'0')||lpad(acc_9_acct,10,'0')
	when acc_id='1' and acc_3_type in ('3','4','6','8') then 'SRC1-'||lpad(acc_ctl1,4,'0')||lpad(acc_ctl2,4,'0')||
	lpad(acc_ctl3,4,'0')||lpad(acc_ctl4,4,'0')||lpad(acc_acct,10,'0')
	when acc_id='2' and acc_2_type in ('3','4','6','8') then 'SRC1-'||lpad(acc_2_ctl1,4,'0')||lpad(acc_2_ctl2,4,'0')||
	lpad(acc_2_ctl3,4,'0')||lpad(acc_2_ctl4,4,'0')||lpad(acc_2_acct,10,'0')
	else null end
	as origntr_acct_id, 
	case when acc_id in ('1','3','2','9','10') then 
	concat(acc_ent_desc,'|',acc_2_univ_desc) else null end as tran_desc,--acc_cust_desc is missing
	case 
	when acc_id='3' then 
		concat(lpad(acc_3_ctl1,4,'0'),lpad(acc_3_ctl2	,4,'0'),lpad(acc_3_ctl3	,4,'0'),lpad(acc_3_ctl4	,4,'0'),lpad(acc_3_ctl4	,4,'0'),lpad(acc_3_acct	,10,'0'),acc_3_ccyyddd,acc_3_rec_seq)
	when acc_id='10' then 
		concat(lpad(acc_10_ctl1,4,'0'),lpad(acc_10_ctl2	,4,'0'),lpad(acc_10_ctl3	,4,'0'),lpad(acc_10_ctl4	,4,'0'),lpad(acc_10_ctl4	,4,'0'),lpad(acc_10_acct	,10,'0'),acc_10_ccyyddd,acc_10_rec_seq)
	when acc_id='9' then 
		concat(lpad(acc_9_ctl1,4,'0'),lpad(acc_9_ctl2	,4,'0'),lpad(acc_9_ctl3	,4,'0'),lpad(acc_9_ctl4	,4,'0'),lpad(acc_9_ctl4	,4,'0'),lpad(acc_9_acct	,10,'0'),acc_9_ccyyddd,acc_9_rec_seq)
	when acc_id='1' then 
		concat(lpad(acc_ctl1,4,'0'),lpad(acc_ctl2	,4,'0'),lpad(acc_ctl3	,4,'0'),lpad(acc_ctl4	,4,'0'),lpad(acc_ctl4	,4,'0'),lpad(acc_acct	,10,'0'),acc_ccyyddd,acc_rec_seq)
	when acc_id='2' then 
		concat(lpad(acc_2_ctl1,4,'0'),lpad(acc_2_ctl2	,4,'0'),lpad(acc_2_ctl3	,4,'0'),lpad(acc_2_ctl4	,4,'0'),lpad(acc_2_ctl4	,4,'0'),lpad(acc_2_acct	,10,'0'),acc_2_ccyyddd,acc_2_rec_seq)
	
	else
	NULL end as tran_ref_no,
	case 
	when acc_id='1' then acc_usr_tr_cd 
	when acc_id='3' then acc_3_usr_tr_cd
	when acc_id='10' then acc_10_usr_tr_cd
	when acc_id='09' then acc_9_usr_tr_cd
	when acc_id='2' then acc_2_usr_tr_cd
	
	else NULL end as tran_prod_type_cd_tmp,
	
	
	null as tran_acct1_tmp,null as  tran_amt_tmp,null as  tran_dt_tmp,null as tran_type_cd_tmp,
	current_date as dl_as_of_dt,
	'SRC1' as dl_source_cd,

	acc_ident,
	case when acc_id='1' then acc_amt 
	when acc_id='3' then acc_3_amt
	when acc_id='10' then acc_10_amt
	when acc_id='9' then acc_9_amt
	when acc_id='2' then acc_2_amt
	else null end as tran_amnt_act_cur
	from (
SELECT 'SRC1_STG1' as mapping,
	acc_ctl1, acc_ctl2, acc_ctl3, acc_ctl4, acc_acct, acc_ccyyddd, acc_rec_seq, acc_id, acc_amt,
	acc_pst_dt, acc_usr_tr_cd, acc_type, acc_desc, acc_2_ctl1, acc_2_ctl2, acc_2_ctl3, acc_2_ctl4, 
	acc_2_acct, acc_2_ccyyddd, acc_2_rec_seq, acc_2_amt, acc_2_pst_dt, acc_2_usr_tr_cd, acc_2_type, 
	acc_2_univ_desc, acc_3_ctl1, acc_3_ctl2, acc_3_ctl3, acc_3_ctl4, acc_3_acct, acc_3_ccyyddd, 
	acc_3_rec_seq, acc_3_amt, acc_3_usr_tr_cd, acc_3_type, acc_ent_desc, acc_ent_dt, acc_9_ctl1,
	acc_9_ctl2, acc_9_ctl3, acc_9_ctl4, acc_9_acct, acc_9_ccyyddd, acc_9_rec_seq, acc_9_amt,
	acc_9_usr_tr_cd, acc_9_type, acc_desc_cd, acc_dt_cd, acc_9_univ_desc, acc_10_ctl1, acc_10_ctl2, 
	acc_10_ctl3, acc_10_ctl4, acc_10_acct, acc_10_ccyyddd, acc_10_rec_seq, acc_10_amt, acc_10_usr_tr_cd, 
	acc_10_type, acc_ud_desc, dl_as_of_dt, dl_source_cd, acc_ident
	FROM "DEMO2"."SRC1_STG1")STAGING1))t
where	tran_ref_no=cast(:txn_ref_no as varchar(50))
'''


#SRC2_STAGING_DATA1 & SRC2_STAGING_DATA2  TO STG_SRC2_KDE
########################################################

stg_src2_KDE_query='''SELECT 'SRC2_KDE' as mapping, drcr_in, origntr_acct_id, tran_acct1_tmp, 
	cast(cast(tran_amt_tmp as int)/100.0 as varchar(20))  as tran_amt_tmp,
	to_date(tran_dt_tmp,'dd-mon-yy') as tran_dt_tmp
	, to_date(dl_as_of_dt,'dd-mon-yy') as dl_as_of_dt
	, dl_source_cd, txn_amt	, acc_ident_nbr   
	FROM "DEMO2"."SRC2_KDE"
	where tran_amt_tmp=:tranamt 
	and cast(tran_dt_tmp as date)=cast(:trandate as date)
	
UNION
	
(
	
WITH SRC2_STG1_CTE AS (
SELECT 'SRC2_STG1' as mapping, nacha_050_coll_file_no, nacha_5, dl_as_of_dt, dl_source_cd, nacha_050_coll_btch_no, ifw_eff_dt, nacha_050_coll_pt
	FROM "DEMO2"."SRC2_STG1"
),
SRC2_STG2_CTE AS (	
SELECT 'SRC2_STG2' as mapping,nacha_060_coll_file_no,nacha_6, dl_as_of_dt, dl_source_cd, nacha_060_dtl_par, nacha_060_coll_btch_no, ifw_eff_dt, nacha_060_coll_pt
	FROM "DEMO2"."SRC2_STG2"
),
JOINS_SRC_CTES AS ( select b.*,a.* from SRC2_STG1_CTE a 
	join  SRC2_STG2_CTE b
	on a.nacha_050_coll_file_no=b.nacha_060_coll_file_no
	and a.nacha_050_coll_btch_no=b.nacha_060_coll_btch_no
	)
	select * from (
Select
'SRC2-STG2' ,
drcr_in,
case when drcr_in='C' then substr(nacha_5,41,10)
		when drcr_in='D' and IAT_ind='Y' then substr(nacha_6, 40, 35)
		when drcr_in='D' and IAT_ind!='Y' then substr(nacha_6, 13, 17)
		end origntr_acct_id,
Case when IAT_ind='Y' then substr(substr(nacha_6,40,35),-17)
	else lpad(substr(nacha_6,13,17),17,'0')
	end tran_acct1_tmp,
cast(cast(substr(nacha_6, 30, 10) as int)/100.0 as varchar(10)) as tran_amt_tmp,
to_date(substr(nacha_5,70,6),'yyMMdd') as tran_dt_tmp,
CURRENT_DATE as dl_as_of_dt,
'SRC1' as dl_source_cd,
cast(cast(substr(nacha_6, 30, 10) as int)/100.0  as varchar(20)) as txn_amt,
Case when substr(nacha_5,51,3) in ('CIE','MTE') then trim(substr(nacha_6,55,15))
	when substr(nacha_5,51,3) ='POP' then trim(substr(nacha_6,40,15))
	when substr(nacha_5,51,3) ='SHR' then trim(substr(nacha_6,44,11))
	when substr(nacha_5,51,3) = 'IAT' then trim(substr(nacha_6 ,4,15)) 
	else  trim(substr(nacha_6,40,15)) end acc_ident_nbr
From
(
select case when substr(nacha_6,2,2) in ('21','62','23','22','54','53','52','51','44','43','42','41','34','33','32','31') then 'C'
	else 'D' end drcr_in,
	case when substr (nacha_5,51,3)='IAT' then 'Y'
	else 'N' end IAT_ind,
	a.*
from JOINS_SRC_CTES a
))
 	where tran_amt_tmp=:tranamt
	and cast(tran_dt_tmp as date)=cast(:trandate as date)
	);'''




#SRC1_FILE TO SRC1_STAGING_DATA;
###################################

src1_Staging_data='''
	SELECT 'SRC1_DATA' as map, acc_ctl1, acc_ctl2, acc_ctl3, acc_ctl4, acc_acct, acc_ccyyddd,
		acc_rec_seq, acc_id, acc_amt, acc_pst_dt, acc_usr_tr_cd, acc_type, acc_desc, acc_2_ctl1,
		acc_2_ctl2, acc_2_ctl3, acc_2_ctl4, acc_2_acct, acc_2_ccyyddd, acc_2_rec_seq, acc_2_amt,
		acc_2_pst_dt, acc_2_usr_tr_cd, acc_2_type, acc_2_univ_desc, acc_3_ctl1, acc_3_ctl2, acc_3_ctl3,
		acc_3_ctl4, acc_3_acct, acc_3_ccyyddd, acc_3_rec_seq, acc_3_amt, acc_3_usr_tr_cd, acc_3_type, 
		acc_ent_desc, acc_ent_dt, acc_9_ctl1, acc_9_ctl2, acc_9_ctl3, acc_9_ctl4, acc_9_acct, acc_9_ccyyddd,
		acc_9_rec_seq, acc_9_amt, acc_9_usr_tr_cd, acc_9_type, acc_desc_cd, acc_dt_cd, acc_9_univ_desc,
		acc_10_ctl1, acc_10_ctl2, acc_10_ctl3, acc_10_ctl4, acc_10_acct, acc_10_ccyyddd, acc_10_rec_seq, 
		acc_10_amt, acc_10_usr_tr_cd, acc_10_type, acc_ud_desc, dl_as_of_dt, dl_source_cd, acc_ident
	FROM "DEMO2"."SRC1_DATA"
	
	where (
(concat(lpad(acc_3_ctl1,4,'0'),lpad(acc_3_ctl2,4,'0'),lpad(acc_3_ctl3,4,'0'),lpad(acc_3_ctl4,4,'0'),lpad(acc_3_acct	,10,'0'),acc_3_ccyyddd,acc_3_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_10_ctl1,4,'0'),lpad(acc_10_ctl2,4,'0'),lpad(acc_10_ctl3,4,'0'),lpad(acc_10_ctl4,4,'0'),
		lpad(acc_10_acct	,10,'0'),acc_10_ccyyddd,acc_10_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_9_ctl1,4,'0'),lpad(acc_9_ctl2,4,'0'),lpad(acc_9_ctl3,4,'0'),lpad(acc_9_ctl4,4,'0'),
		lpad(acc_9_acct,10,'0'),acc_9_ccyyddd,acc_9_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_2_ctl1,4,'0'),lpad(acc_2_ctl2,4,'0'),lpad(acc_2_ctl3,4,'0'),lpad(acc_2_ctl4,4,'0'),
		lpad(acc_2_acct,10,'0'),acc_2_ccyyddd,acc_2_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_ctl1,4,'0'),lpad(acc_ctl2,4,'0'),lpad(acc_ctl3,4,'0'),lpad(acc_ctl4,4,'0'),
		lpad(acc_acct,10,'0'),acc_ccyyddd,acc_rec_seq)
=cast(:txn_ref_no as varchar(50)))


		)

	
	UNION
		
SELECT 'SRC1_STG1',acc_ctl1, acc_ctl2, acc_ctl3, acc_ctl4, acc_acct, acc_ccyyddd,
		acc_rec_seq, acc_id, acc_amt, acc_pst_dt, acc_usr_tr_cd, acc_type, acc_desc,
		acc_2_ctl1, acc_2_ctl2, acc_2_ctl3, acc_2_ctl4, acc_2_acct, acc_2_ccyyddd, 
		acc_2_rec_seq, acc_2_amt, acc_2_pst_dt, acc_2_usr_tr_cd, acc_2_type, acc_2_univ_desc, 
		acc_3_ctl1, acc_3_ctl2, acc_3_ctl3, acc_3_ctl4, acc_3_acct, acc_3_ccyyddd, acc_3_rec_seq,
		acc_3_amt, acc_3_usr_tr_cd, acc_3_type, acc_ent_desc, acc_ent_dt, acc_9_ctl1, acc_9_ctl2,
		acc_9_ctl3, acc_9_ctl4, acc_9_acct, acc_9_ccyyddd, acc_9_rec_seq, acc_9_amt, acc_9_usr_tr_cd,
		acc_9_type, acc_desc_cd, acc_dt_cd, acc_9_univ_desc, acc_10_ctl1, acc_10_ctl2, acc_10_ctl3, 
		acc_10_ctl4, acc_10_acct, acc_10_ccyyddd, acc_10_rec_seq, acc_10_amt, acc_10_usr_tr_cd, 
		acc_10_type, acc_ud_desc, dl_as_of_dt, dl_source_cd, acc_ident
	FROM "DEMO2"."SRC1_STG1"

where 
(
(concat(lpad(acc_3_ctl1,4,'0'),lpad(acc_3_ctl2,4,'0'),lpad(acc_3_ctl3,4,'0'),lpad(acc_3_ctl4,4,'0'),lpad(acc_3_acct	,10,'0'),acc_3_ccyyddd,acc_3_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_10_ctl1,4,'0'),lpad(acc_10_ctl2,4,'0'),lpad(acc_10_ctl3,4,'0'),lpad(acc_10_ctl4,4,'0'),
		lpad(acc_10_acct	,10,'0'),acc_10_ccyyddd,acc_10_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_9_ctl1,4,'0'),lpad(acc_9_ctl2,4,'0'),lpad(acc_9_ctl3,4,'0'),lpad(acc_9_ctl4,4,'0'),
		lpad(acc_9_acct,10,'0'),acc_9_ccyyddd,acc_9_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_2_ctl1,4,'0'),lpad(acc_2_ctl2,4,'0'),lpad(acc_2_ctl3,4,'0'),lpad(acc_2_ctl4,4,'0'),
		lpad(acc_2_acct,10,'0'),acc_2_ccyyddd,acc_2_rec_seq)
=cast(:txn_ref_no as varchar(50)))
or
(concat(lpad(acc_ctl1,4,'0'),lpad(acc_ctl2,4,'0'),lpad(acc_ctl3,4,'0'),lpad(acc_ctl4,4,'0'),
		lpad(acc_acct,10,'0'),acc_ccyyddd,acc_rec_seq)
=cast(:txn_ref_no as varchar(50)))

		
)
	;'''



#SRC2_FILE1 TO SRC2_STAGING_DATA1
###################################


src2_Staging_data='''SELECT 'STG' as "Type", *
	FROM "DEMO2"."SRC2_DATA1"
	WHERE 
 "nacha_050_coll_file_no" = cast(:nachafile as varchar(50))	\
		and "nacha_050_coll_btch_no" = cast(:nachabatch as varchar(50)) \
	
UNION 
SELECT 'SRC2 STG1',*
	FROM "DEMO2"."SRC2_STG1"
	WHERE 
	 "nacha_050_coll_file_no" = cast(:nachafile as varchar(20))	\
		and "nacha_050_coll_btch_no" = cast(:nachabatch as varchar(20)) \
	;'''


#SRC2_FILE2 TO SRC2_STAGING_DATA2	

src2_Staging_data2='''SELECT 'STG' as "Type",*
	FROM "DEMO2"."SRC2_DATA2"
	WHERE 
	 "nacha_060_coll_file_no" = cast(:nachafile as varchar(50))	\
		and "nacha_060_coll_btch_no" = cast(:nachabatch as varchar(50)) \
	
UNION 
SELECT 'SRC',*
	FROM "DEMO2"."SRC2_STG2"
WHERE 
	 "nacha_060_coll_file_no" = cast(:nachafile as varchar(20))	\
		and "nacha_060_coll_btch_no" = cast(:nachabatch as varchar(20)) \
	;'''


def print_response(db_response,description):
    st.write(description)
    if(db_response is not None and len(db_response)>0):
          choice_default_mod = pd.DataFrame.from_dict(eval(db_response))
          st.table(choice_default_mod)
    else:
        st.write('No Data available')

    #print(tabulate.tabulate(response,headers='keys', tablefmt="pretty"))



def display_lineage(order,txn_ref_no):
    print(txn_ref_no)
   
    param_value=SQLUtility.execute(GET_ADDITIONAL_PARAMS,parameters={'txn_ref_no':txn_ref_no})
    
    lst_value=[]
    if(len(param_value)>0):
         print(param_value)
         lst_value=eval(param_value)
         print(len(lst_value))
    if(len(lst_value)==0):
        print_response(None,'No Matching records found for '+txn_ref_no)
        exit(0)
        
    tran_amt=lst_value[0]['txn_amt']
    tran_acct=lst_value[0]['account_number']
    tran_date=lst_value[0]['txn_value_date']
    
    nacha_value=SQLUtility.execute(GET_NACHA_PARAMS,parameters={'tranamnt':tran_amt,'trandate':tran_date})
    
    lst_nacha_values=[]
    if(len(nacha_value)>0):
        print(nacha_value)
        lst_nacha_values=eval(nacha_value)
    if(len(lst_nacha_values)==0):
        print_response(None,'Nacha Params unavailable')
        exit(0)
        
    nacha5file=lst_nacha_values[0]['nacha_050_coll_file_no']
    nacha5batch=lst_nacha_values[0]['nacha_050_coll_btch_no']
    
    st.write('Values Parsed: Tran Amt:{0}, Tran Date:{1}, Tran Acct:{2}, txn_ref_no:{3} , nacha5col:{4} , nacha5batch:{5}'
             .format(tran_amt,tran_date,tran_acct,txn_ref_no,nacha5file,nacha5batch))
    

    #print(json.loads(param_value))
    #Bottom to Top
    
    if(order == 1):
        response=SQLUtility.execute(stg_src1_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Source 1 to Stage')
        
        response=SQLUtility.execute(src2_Staging_data2,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Source 2 Staging Data')

        response=SQLUtility.execute(src1_Staging_data,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Source 1 Staging data')

        response=SQLUtility.execute(src2_Staging_data,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Source 2 Staging Data')
     
        response=SQLUtility.execute(stg_src2_KDE_query,parameters={'tranamt':tran_amt,'trandate':tran_date,'tranacct':tran_acct})
        print_response(response,'Stage Source 2 to KDE')

        response=SQLUtility.execute(stg_src1_KDE_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Stage Source 1 to KDE')

        response=SQLUtility.execute(KDE_To_Stitch_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'KDE to Stitching')
#{'tranamt':tran_amt,'trandate':tran_date,'tranacct':tran_acct}
        response=SQLUtility.execute(stitch_to_precsa_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Stitching to Pre CSA')

        response=SQLUtility.execute(precsa_csa,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Pre CSA to CSA')

        resp=SQLUtility.execute(query,parameters={'txn_ref_no':txn_ref_no})
        print_response(resp,'CSA')
        #Top to Bottom
    elif order == 2:
        resp=SQLUtility.execute(query,parameters={'txn_ref_no':txn_ref_no})
        print_response(resp,'CSA')
        response=SQLUtility.execute(precsa_csa,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Pre CSA to CSA')
        response=SQLUtility.execute(stitch_to_precsa_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Stitching to Pre CSA')
        response=SQLUtility.execute(KDE_To_Stitch_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'KDE to Stitching')
        response=SQLUtility.execute(stg_src1_KDE_query,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Stage Source 1 to KDE')
        response=SQLUtility.execute(stg_src2_KDE_query,parameters={'tranamt':tran_amt,'trandate':tran_date,'tranacct':tran_acct})
        print_response(response,'Stage Source 2 to KDE')
        response=SQLUtility.execute(src2_Staging_data,parameters={'nachafile':nacha5file,'nachabatch':nacha5batch})
        print_response(response,'Source 2 Staging Data')
        response=SQLUtility.execute(src1_Staging_data,parameters={'txn_ref_no':txn_ref_no})
        print_response(response,'Source 1 Staging data')
        response=SQLUtility.execute(src2_Staging_data2,parameters={'nachafile':nacha5file,'nachabatch':nacha5batch})
        print_response(response,'Source 2 Staging Data')
       # response=SQLUtility.execute(stg_src1_query,parameters={'txn_ref_no':txn_ref_no})
        #print_response(response,'Stage to Source 1')
    #cypher_query=mapping_template_expanded.format('CSA',tran_amt,tran_acct,tran_date)
    #st.write(cypher_query)
    #print('Plotting Graph')
    #fig=pg.get_graph_in_streamlit(cypher_query)
    #st.plotly_chart(fig) 
    

def get_the_results(order,txn_ref_no):
    print('=================================================')
    print(order)
    display_lineage(order,txn_ref_no)
    
def look_for_records(q):
    try:
        print(q)
        print('inside look_for_records')

    except:
         print('exception occured')
