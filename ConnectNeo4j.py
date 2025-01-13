from neo4j import GraphDatabase
from ConnectPostGres import connect_pg
import Configs

# Connect to Neo4j
neo4j_driver = GraphDatabase.driver(
    uri=Configs.Neo4JS_DB_Url,  # Your Neo4j bolt address
    auth=(Configs.NEO4JS_DB_User, Configs.NEO4JS_DB_Password)
)

def fetch_data_from_neo4j():
    
    session= neo4j_driver.session()
    
    # result = session.run("match (n:csa) return n")
    # for record in result:
    #     print(record)
    cur = connect_pg() 
    
    #Cleanup command:
    #Create relation precsa- csa
    CleanupCmd  =  "MATCH (n) detach delete n "
                        
    #relationship
    print ("Cleanup  Command: ", CleanupCmd)
    session.run(CleanupCmd)
    
     # #############################################################################
    # Create CSA Node and relations
    ##############################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."FIN_ACCT_TXNS"')
    rows = cur.fetchall()
    
    for item in rows:
        CsaCmd = "create (n: CSA {name : 'FIN_ACCT_TXNS', txn_ref_no : '" + str (item[0]) + "', fic_mis_date : '" + str (item[1]) + "' , account_number : '" + str (item[2]) +"' \
        , txn_value_date : '" + str (item[3]) +"' , drcr_indicator : '" + str (item[4]) +"' , txn_desc : '" + str (item[5]) +"', TRtran_prod_type_cd_tmp : '" + str (item[6]) +"', \
        txn_amt : '" + str (item[7]) + "', txn_amt_acy : '" + str (item[8]) +"' })"
        
                
        #relationship
        print ("CSA Command: ", CsaCmd)
        session.run(CsaCmd)
        
    
    # #############################################################################
    # Create PRE-CSA Node and relations
    ##############################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."PRE_FIN_ACC_TXNS"')
    rows = cur.fetchall()
    
    for item in rows:
        
        PreCsaCmd = "create (n: PRECSA {name : 'PRE_FIN_ACC_TXNS', txn_ref_no : '" + str (item[0]) + "', fic_mis_date : '" + str (item[1]) + "' , account_number : '" + str (item[2]) +"' \
        , txn_value_date : '" + str (item[3]) +"' , drcr_indicator : '" + str (item[4]) +"' , txn_desc : '" + str (item[5]) +"', TRtran_prod_type_cd_tmp : '" + str (item[6]) +"', txn_amt : '" + str (item[7]) + "', txn_amt_acy : '" + str (item[8]) +"' \
        })"" "  
        
    
        #relationship
        print ("PreCSACommand: ", PreCsaCmd)
        session.run(PreCsaCmd)
        
    #Create relation precsa- csa
    CsaPreCsaRelCmd  =  "MATCH (A:CSA), (B:PRECSA) where TRIM(A.txn_ref_no) = TRIM(B.txn_ref_no) \
                        CREATE (A) <-[r:Extr_from_precsa]- (B)\
                        RETURN A, B; "
                        
    #relationship
    print ("Relation Command: ", CsaPreCsaRelCmd)
    session.run(CsaPreCsaRelCmd)
    
    
    # ##############################################################################
    # Create Stitch Node & relations
    ################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."SRC1_STITCHED"')
    rows = cur.fetchall()
    
    for item in rows:
        StichCmd = "create (n: STITCH { name : 'SRC1_STITCHED', bnf_acct_id : '" + str (item[0]) + "', drcr_in : '" + str (item[1]) + "' , tran_val_dt : '" + str (item[2]) +"' \
        , origintr_acct_id : '" + str (item[3]) +"' , tran_desc : '" + str (item[4]) +"' , tran_prod_type_cd_tmp : '" + str (item[5]) +"', tran_ref_no : '" + str (item[6]) +"' \
        , origintr_acct_id : '" + str (item[7]) +"' , dl_as_of_dt : '" + str (item[8]) +"' , dl_source_cd : '" + str (item[9]) +"', txn_amt : '" + str (item[10]) +"' \
        , tran_grp_cd_tmp : '" + str (item[11]) +"' , stitch_flag : '" + str (item[12]) +"' , tran_acct1_tmp : '" + str (item[13]) +"', tran_amt_tmp : '" + str (item[14]) +"' \
        , tran_dt_tmp : '" + str (item[15]) +"', tran_type_cd_tmp : '" + str (item[16]) +"' , tran_amnt_act_cur :'" + str (item[17]) +"' , lkp_tran_ref_no : '" + str (item[18]) +"'\
        })"" " 
        
        	
        #relationship
        print ("StitchCommand: ", StichCmd)
        session.run(StichCmd)
        
    #Create relation stitch- precsa
    PreCsaStchRelCmd  =  "MATCH (A:PRECSA), (B:STITCH) where  TRIM(A.txn_ref_no) = TRIM(B.tran_ref_no) \
                        CREATE (A) <-[r:Extr_from_stitch]- (B) RETURN A, B; "
                        
                        
     #relationship
    print ("Command: ", StichCmd)
    session.run(PreCsaStchRelCmd)  
        
    # #############################################################################
    # Create KDES Nodes & relations with stg
    ####################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."SRC1_KDE"')
    KDE1rows = cur.fetchall()
    
    cur.execute('SELECT * FROM "DEMO2"."SRC2_KDE"')
    KDE2rows = cur.fetchall()
    
    for item in KDE1rows:
        kde1Cmd = "create (n: KDE1 { name : 'SRC1_KDE', tran_amnt : '" + str (item[0]) + "', bnf_acct_id : '" + str (item[1]) + "' , drcr_in : '" + str (item[2]) +"' \
        , tran_val_dt : '" + str (item[3]) +"' , origntr_acct_id : '" + str (item[4]) +"' , tran_desc : '" + str (item[5]) +"' , tran_ref_no : '" + str (item[6]) +"' \
        , tran_prod_type_cd_tmp : '" + str (item[7]) +"' , tran_acct1_tmp : '" + str (item[8]) +"' , tran_amt_tmp : '" + str (item[9]) +"' , tran_dt_tmp : '" + str (item[10]) +"' \
        , tran_type_cd_tmp : '" + str (item[11]) +"' , dl_as_of_dt : '" + str (item[12]) +"' , dl_source_cd : '" + str (item[13]) +"' , bnf_acct_id_type : '" + str (item[14]) +"' \
       , origntr_acct_id_type : '" + str (item[15]) +"' , acc_ident : '" + str (item[16]) +"' , tran_amnt_act_cur : '" + str (item[17]) +"' \
        })"" " 
        session.run(kde1Cmd)
        
       
    for item in KDE2rows:
        kde2Cmd = "create (n: KDE2 { name : 'SRC2_KDE', drcr_in  : '" + str (item[0]) + "' ,  origntr_acct_id : '" + str (item[1]) +"' \
        , tran_acct1_tmp : '" + str (item[2]) +"' , tran_amt_tmp : '" + str (item[3]) +"', tran_dt_tmp : '" + str (item[4]) + "' \
        , dl_as_of_dt : '" + str (item[5]) +"' , dl_source_cd : '" + str (item[6]) +"' , txn_amt : '" + str (item[7]) +"' , acc_ident_nbr : '" + str (item[8]) +"' \
        , nacha_060_dtl_par : '" + str (item[9]) +"' , nacha_5 : '" + str (item[10]) +"' , nacha_6 : '" + str (item[11]) +"' \
        })"" "
        session.run(kde2Cmd)
        
     
    #Create relation stitch- kde1
    
    stchtokde2relcmd  =  "match (A:STITCH),  (B:KDE2) where  \
                               A.lkp_tran_ref_no = B.nacha_060_dtl_par \
                            create (A) <-[r:Extr_from_kde2_to_Stitch]- (B) \
                            return A,B"
    
    #  #Create relation stitch- kd2
    StchToKde1RelCmd  =  "MATCH (A:STITCH), (C:KDE1) where  trim(A.tran_ref_no) = trim(C.tran_ref_no) \
                            CREATE (A) <-[r2:Extr_from_kde1_to_stich]- (C) \
                            RETURN A, C; "
                        
    #relationship
    print ("Stch to kde Relation Command: ", StchToKde1RelCmd)
    session.run(stchtokde2relcmd)
    session.run(StchToKde1RelCmd)
    
    
    # ##############################################################################
    # Create HOLDING Node & relations
    ################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."SRC1_HOLD"')
    rows = cur.fetchall()
    
    for item in rows:
        HoldingCmd = "create (n: HOLDING { name : 'SRC1_HOLD', tran_amnt : '" + str (item[0]) + "', bnf_acct_id : '" + str (item[1]) + "' , drcr_in : '" + str (item[2]) +"' \
        , tran_val_dt : '" + str (item[3]) +"' , origntr_acct_id : '" + str (item[4]) +"' , tran_desc : '" + str (item[5]) +"', tran_ref_no : '" + str (item[6]) +"'\
        , tran_prod_type_cd_tmp : '" + str (item[7]) +"' , tram_acct1_tmp : '" + str (item[8]) +"' , tran_amt_tmp : '" + str (item[9]) +"', tran_dt_tmp : '" + str (item[10]) +"'\
        , tran_type_cd_tmp : '" + str (item[11]) +"' , bnf_acct_id_type : '" + str (item[12]) +"' , orrigntr_acct_id_type : '" + str (item[13]) +"', acc_ident : '" +\
        str (item[14]) +"'  \
        })"" " 
        
        #relationship
        print ("Holding Command: ", HoldingCmd)
        session.run(HoldingCmd)
        
    #Create relation holding- stitch
    HoldingStchRelCmd  =  "MATCH (A:HOLDING), (B:KDE1) where  trim(A.tran_ref_no) = trim(B.tran_ref_no) \
                        CREATE (A) <-[r:Extr_from_kde_to_hld]- (B) \
                        RETURN A, B; "
    
     #relationship
    print ("Command: ", HoldingStchRelCmd)
    session.run(HoldingStchRelCmd)  
    
    
    
    # ##############################################################################
    # Create Orphan Node & relations
    ################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."SRC1_ORPHAN"')
    rows = cur.fetchall()
    
    for item in rows:
        HoldingCmd = "create (n: ORPHAN { name : 'SRC1_ORPHAN', tran_amnt : '" + str (item[0]) + "', bnf_acct_id : '" + str (item[1]) + "' , drcr_in : '" + str (item[2]) +"' \
        , tran_val_dt : '" + str (item[3]) +"' , origntr_acct_id : '" + str (item[4]) +"' , tran_desc : '" + str (item[5]) +"', tran_ref_no : '" + str (item[6]) +"'\
        , tran_prod_type_cd_tmp : '" + str (item[7]) +"' , tram_acct1_tmp : '" + str (item[8]) +"' , tran_amt_tmp : '" + str (item[9]) +"', tran_dt_tmp : '" + str (item[10]) +"'\
        , tran_type_cd_tmp : '" + str (item[11]) +"' , bnf_acct_id_type : '" + str (item[12]) +"' , orrigntr_acct_id_type : '" + str (item[13]) +"', acc_ident : '" +\
        str (item[14]) +"'  \
        })"" " 
        
        #relationship
        print ("Holding Command: ", HoldingCmd)
        session.run(HoldingCmd)
        
    #Create relation holding- stitch
    HoldingStchRelCmd  =   "MATCH (A:ORPHAN), (B:KDE1)   where A.tran_ref_no = B.tran_ref_no\
            CREATE (A) <-[r:Extr_from_KD1_to_orphan]- (B) RETURN A, B " 
    
     #relationship
    print ("Command: ", HoldingStchRelCmd)
    session.run(HoldingStchRelCmd)  
    
    
    
    # ##############################################################################
    # Create EXCP Node & relations WITH STITCH
    ################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."EXCEPTION_TBL"')
    rows = cur.fetchall()
    
    for item in rows:
        ExcpCmd = "create (n: EXCEPTION { name : 'EXCEPTION_TBL', EXCP_ID : '" + str (item[0]) + "', entity_cd : '" + str (item[1]) + "' , QC_ID : '" + str (item[2]) +"' \
        , CONCAT_FLD_VAL : '" + str (item[3]) +"' , COL_NM : '" + str (item[4]) +"' , COL_VAL : '" + str (item[5]) +"', DL_AS_OF_DT : '" +\
        str (item[6]) +"' , create_dt : '"  + str (item[7]) +"' , run_id : " + str (item[8]) +" , tran_amnt : '" + str (item[9]) +"', tran_ref_no : '" +\
        str (item[10])  +"'  \
        })"" " 
        
        #relationship
        print ("Exception Command: ", ExcpCmd)
        session.run(ExcpCmd)
        
    #Create relation stitch- precsa
    ExcpStchRelCmd  =  "MATCH (A:EXCEPTION), (B:STITCH) where  TRIM(A.tran_ref_no) = TRIM(B.tran_ref_no) \
                        CREATE (A) <-[r:Extr_from_stitch_to_excp]- (B) RETURN A, B; "
    
     #relationship
    print ("Exception Command: ", ExcpCmd)
    session.run(ExcpStchRelCmd)     
    
    
    ####################################################################################
    ###Create stage Nodes to kde nodes
    ##################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."SRC1_STG1"')
    Src1Stgrows = cur.fetchall()
    
    cur.execute('SELECT * FROM "DEMO2"."SRC2_STG1"')
    Src2Stg1rows = cur.fetchall()
    
    cur.execute('SELECT * FROM "DEMO2"."SRC2_STG2"')
    Src2Stg2rows = cur.fetchall()
        
    for item in Src1Stgrows:
        Src1Stgmd = "create (n: SRC1_STG { name : 'SRC1_STG1', acc_ctl1  : '" + str (item[0]) + "' ,  acc_ctl2 : '" + str (item[1]) +"' \
        , acc_ctl3 : '" + str (item[2]) +"' , acc_ctl4 : '" + str (item[3]) +"', acc_acct : '" + str (item[4]) +"' , acc_ccyyddd : '" + str (item[5]) +"'  \
        , acc_rec_seq : '" + str (item[6]) +"' , acc_id : '" + str (item[7]) +"' , acc_amt : '" + str (item[8]) +"' , acc_pst_dt : '" + str (item[9]) +"' \
        , acc_usr_tr_cd : '" + str (item[10]) +"', acc_type : '" + str (item[11]) +"' , acc_desc : '" + str (item[12]) +"', acc_2_ctl1 : '" + str (item[13]) +"' \
		, acc_2_ctl2 : '" + str (item[14]) +"' , acc_2_ctl3 : '" + str (item[15]) +"', acc_2_ctl4 : '" + str (item[16]) +"' , acc_2_acct : '" + str (item[17]) +"'  \
        , acc_2_ccyyddd : '" + str (item[18]) +"' , acc_2_rec_seq : '" + str (item[19]) +"' , acc_2_amt : '" + str (item[20]) +"' , acc_2_pst_dt : '" + str (item[21]) +"' \
        , acc_2_usr_tr_cd : '" + str (item[22]) +"' , acc_2_type : '" + str (item[23]) +"' , acc_2_univ_desc : '" + str (item[24]) +"', acc_3_ctl1 : '" + str (item[25]) +"' \
		, acc_3_ctl2 : '" + str (item[26]) +"' , acc_3_ctl3 : '" + str (item[27]) +"', acc_3_ctl4 : '" + str (item[28]) +"' , acc_3_acct : '" + str (item[29]) +"'  \
        , acc_3_ccyyddd : '" + str (item[30]) +"' , acc_3_rec_seq : '" + str (item[31]) +"' , acc_3_amt : '" + str (item[32]) +"' , acc_3_usr_tr_cd : '" + str (item[33]) +"' \
        , acc_3_type : '" + str (item[34]) +"', acc_ent_desc : '" + str (item[35]) +"' , acc_ent_dt : '" + str (item[36]) +"', acc_9_ctl1 : '" + str (item[37]) +"' \
		, acc_9_ctl2 : '" + str (item[38]) +"' , acc_9_ctl3 : '" + str (item[39]) +"', acc_9_ctl4 : '" + str (item[40]) +"' , acc_9_acct : '" + str (item[41]) +"'  \
		, acc_9_ccyyddd : '" + str (item[42]) +"' , acc_9_rec_seq : '" + str (item[43]) +"' , acc_9_amt : '" + str (item[44]) +"' , acc_9_usr_tr_cd : '" + str (item[45]) +"' \
	    , acc_9_type : '" + str (item[46]) +"' , acc_desc_cd : '" + str (item[47]) +"' , acc_dt_cd : '" + str (item[48]) +"' \
        , acc_9_univ_desc : '" + str (item[49]) +"' , acc_10_ctl1 : '" + str (item[50]) +"' , acc_10_ctl2 : '" + str (item[51]) +"'\
		, acc_10_ctl3 : '" + str (item[52]) + "' , acc_10_ctl4 : '" + str (item[53]) +"' , acc_10_acct : '" + str (item[54]) +"' \
        , acc_10_ccyyddd : '" + str (item[55]) +"', acc_10_rec_seq : '" + str (item[56]) +"' , acc_10_amt : '" + str (item[57]) +"', acc_10_usr_tr_cd : '" + str (item[58]) +"' \
		, acc_10_type : '" + str (item[59]) +"' , acc_ud_desc : '" + str (item[60]) +"', dl_as_of_dt : '" + str (item[61]) +"' , dl_source_cd : '" + str (item[62]) +"'  \
		, acc_ident : '" + str (item[63]) +"'  \
        })"" "
        
        print ("src1 to stg Command: ", Src1Stgmd)
        session.run(Src1Stgmd)
        
        
    for item in Src2Stg1rows:
        Src2Stg1Cmd = "create (n: SRC2_STG1 { name : 'SRC2_STG1', nacha_050_coll_file_no  : '" + str (item[0]) + "' ,  nacha_5 : '" + str (item[1]) +"' \
        , dl_as_of_dt : '" + str (item[2]) +"' , dl_source_cd : '" + str (item[3]) +"' \
        , nacha_050_coll_btch_no : '" + str (item[4]) +"' , ifw_eff_dt : '" + str (item[5]) +"'  , nacha_050_coll_pt : '" + str (item[6]) +"'\
        })"" "
        print ("src2stg1 Command: ", Src2Stg1Cmd)
        session.run(Src2Stg1Cmd)
        
        
    for item in Src2Stg2rows:
        Src2Stg2Cmd = "create (n: SRC2_STG2 { name : 'SRC2_STG2', nacha_6  : '" + str (item[0]) + "' ,  nacha_060_coll_file_no : '" + str (item[1]) +"' \
        , dl_as_of_dt : '" + str (item[2]) +"' , dl_source_cd : '" + str (item[3]) +"' \
            , nacha_060_dtl_par : '" + str (item[4]) +"' , nacha_060_coll_btch_no : '" + str (item[5]) +"'  , ifw_eff_dt : '" + str (item[6]) +"' , nacha_060_coll_pt : '" + str (item[7]) +"'\
        })"" "
        
        print ("Src2 Stg2 Command: ", Src2Stg2Cmd)
        session.run(Src2Stg2Cmd)

  
    # #Create relation kde to stg
    Kde1ToSrc1Stg1RelCmd  =  "MATCH (A:KDE1), (B:SRC1_STG)   where A.tran_ref_no = (    \
            substring('0000',0,case size(B.acc_9_ctl1)  when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end)+ B.acc_9_ctl1 \
            + substring('0000',0,CASE size(B.acc_9_ctl2)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl2  \
            + substring('0000',0,CASE size(B.acc_9_ctl3)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl3 \
            + substring('0000',0,CASE size(B.acc_9_ctl4)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl4  \
            + substring('0000000000',0,CASE size(B.acc_9_acct) when 1 then 9   when 2 then 8  when 3 then 7  when 4 then 6 when 5 then 5  \
            when 6 then 4  when 7 then 3  when 8 then 2  when 9 then 1   when 10 then 0 end	) + B.acc_9_acct + B.acc_9_ccyyddd + B.acc_9_rec_seq ) \
            CREATE (A) <-[r:Extr_from_Src1Stg1_to_kde1]- (B) RETURN A, B "    
    
    session.run(Kde1ToSrc1Stg1RelCmd)
    #add relations betweenn stg2 and kde2
    Kde2ToSrc2Stg1Stg2RelCmd  =  "MATCH (A:KDE2), (B:SRC2_STG1) \
                                where A.nacha_5 = B.nacha_5 \
                                CREATE (A) <-[r1:Extr_from_Src2Stg1_to_kde2]- (B) \
                                RETURN A, B"   
                                
    #add relations betweenn stg2 and kde2
    Kde2ToSrc2Stg2Stg2RelCmd  =  "MATCH (A:KDE2), (C:SRC2_STG2)  \
                                where A.nacha_6 = C.nacha_6 \
                                CREATE (A) <-[r2:Extr_from_Src2Stg2_to_kde2]- (C) \
                                RETURN A, C "  
                                 
  
    session.run(Kde2ToSrc2Stg2Stg2RelCmd)
    session.run(Kde2ToSrc2Stg1Stg2RelCmd)
    
    
    # ##############################################################################
    # Create EXCP relations WITH SOURCE1 STG
    ################################################################################
    
    # #Create relation STG- EXCP
    ExcpSTGRelCmd  =  "MATCH (A:EXCEPTION), (B:SRC1_STG) where  \
                                A.tran_ref_no = (    \
              substring('0000',0,case size(B.acc_9_ctl1)  when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end)+ B.acc_9_ctl1 \
            + substring('0000',0,CASE size(B.acc_9_ctl2)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl2  \
            + substring('0000',0,CASE size(B.acc_9_ctl3)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl3 \
            + substring('0000',0,CASE size(B.acc_9_ctl4)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl4  \
            + substring('0000000000',0,CASE size(B.acc_9_acct) when 1 then 9   when 2 then 8  when 3 then 7  when 4 then 6 when 5 then 5  \
            when 6 then 4  when 7 then 3  when 8 then 2  when 9 then 1   when 10 then 0 end	) + B.acc_9_acct + B.acc_9_ccyyddd + B.acc_9_rec_seq  ) \
            CREATE (A) <-[r:Extr_from_Src1Stg_to_excp]- (B) \
            RETURN A, B  " 
    
    #  #relationship
    # print ("Command: ", ExcpSTGRelCmd)
    session.run(ExcpSTGRelCmd)  
        
    
    ####################################################################################
    ###Create stage Nodes to src  nodes
    ##################################################################################
    
    cur.execute('SELECT * FROM "DEMO2"."SRC1_DATA"')
    Src1File1rows = cur.fetchall()
    
    cur.execute('SELECT * FROM "DEMO2"."SRC2_DATA1"')
    Src2File1rows = cur.fetchall()
    
    cur.execute('SELECT * FROM "DEMO2"."SRC2_DATA2"')
    Src2File2rows = cur.fetchall()
        
    for item in Src1File1rows:
        Src1FileCmd = "create (n: SRC1_DATA { name : 'SRC1_DATA', acc_ctl1  : '" + str (item[0]) + "' ,  acc_ctl2 : '" + str (item[1]) +"' \
        , acc_ctl3 : '" + str (item[2]) +"' , acc_ctl4 : '" + str (item[3]) +"', acc_acct : '" + str (item[4]) +"' , acc_ccyyddd : '" + str (item[5]) +"'  \
        , acc_rec_seq : '" + str (item[6]) +"' , acc_id : '" + str (item[7]) +"' , acc_amt : '" + str (item[8]) +"' , acc_pst_dt : '" + str (item[9]) +"' \
        , acc_usr_tr_cd : '" + str (item[10]) +"', acc_type : '" + str (item[11]) +"' , acc_desc : '" + str (item[12]) +"', acc_2_ctl1 : '" + str (item[13]) +"' \
		, acc_2_ctl2 : '" + str (item[14]) +"' , acc_2_ctl3 : '" + str (item[15]) +"', acc_2_ctl4 : '" + str (item[16]) +"' , acc_2_acct : '" + str (item[17]) +"'  \
        , acc_2_ccyyddd : '" + str (item[18]) +"' , acc_2_rec_seq : '" + str (item[19]) +"' , acc_2_amt : '" + str (item[20]) +"' , acc_2_pst_dt : '" + str (item[21]) +"' \
        , acc_2_usr_tr_cd : '" + str (item[22]) +"' , acc_2_type : '" + str (item[23]) +"' , acc_2_univ_desc : '" + str (item[24]) +"', acc_3_ctl1 : '" + str (item[25]) +"' \
		, acc_3_ctl2 : '" + str (item[26]) +"' , acc_3_ctl3 : '" + str (item[27]) +"', acc_3_ctl4 : '" + str (item[28]) +"' , acc_3_acct : '" + str (item[29]) +"'  \
        , acc_3_ccyyddd : '" + str (item[30]) +"' , acc_3_rec_seq : '" + str (item[31]) +"' , acc_3_amt : '" + str (item[32]) +"' , acc_3_usr_tr_cd : '" + str (item[33]) +"' \
        , acc_3_type : '" + str (item[34]) +"', acc_ent_desc : '" + str (item[35]) +"' , acc_ent_dt : '" + str (item[36]) +"', acc_9_ctl1 : '" + str (item[37]) +"' \
		, acc_9_ctl2 : '" + str (item[38]) +"' , acc_9_ctl3 : '" + str (item[39]) +"', acc_9_ctl4 : '" + str (item[40]) +"' , acc_9_acct : '" + str (item[41]) +"'  \
		, acc_9_ccyyddd : '" + str (item[42]) +"' , acc_9_rec_seq : '" + str (item[43]) +"' , acc_9_amt : '" + str (item[44]) +"' , acc_9_usr_tr_cd : '" + str (item[45]) +"' \
	    , acc_9_type : '" + str (item[46]) +"' , acc_desc_cd : '" + str (item[47]) +"' , acc_dt_cd : '" + str (item[48]) +"' \
        , acc_9_univ_desc : '" + str (item[49]) +"' , acc_10_ctl1 : '" + str (item[50]) +"' , acc_10_ctl2 : '" + str (item[51]) +"'\
		, acc_10_ctl3 : '" + str (item[52]) + "' , acc_10_ctl4 : '" + str (item[53]) +"' , acc_10_acct : '" + str (item[54]) +"' \
        , acc_10_ccyyddd : '" + str (item[55]) +"', acc_10_rec_seq : '" + str (item[56]) +"' , acc_10_amt : '" + str (item[57]) +"', acc_10_usr_tr_cd : '" + str (item[58]) +"' \
		, acc_10_type : '" + str (item[59]) +"' , acc_ud_desc : '" + str (item[60]) +"', dl_as_of_dt : '" + str (item[61]) +"' , dl_source_cd : '" + str (item[62]) +"'  \
		, acc_ident : '" + str (item[63]) +"'  \
        })"" "
        session.run(Src1FileCmd)
        
    for item in Src2File1rows:
        Src2File1Cmd = "create (n: SRC2_DATA1 { name : 'SRC2_DATA1', nacha_050_coll_file_no  : '" + str (item[0]) + "' ,  nacha_5 : '" + str (item[1]) +"' \
        , dl_as_of_dt : '" + str (item[2]) +"' , dl_source_cd : '" + str (item[3]) +"' \
            , nacha_050_coll_btch_no : '" + str (item[4]) +"' , ifw_eff_dt : '" + str (item[5]) +"'  , nacha_050_coll_pt : '" + str (item[6]) +"'\
         })"" "
        session.run(Src2File1Cmd)
        
    for item in Src2File2rows:
        Src2File2Cmd = "create (n: SRC2_DATA2 { name : 'SRC2_DATA2',  nacha_6  : '" + str (item[0]) + "' ,  nacha_060_coll_file_no : '" + str (item[1]) +"' \
        , dl_as_of_dt : '" + str (item[2]) +"' , dl_source_cd : '" + str (item[3]) +"' \
            , nacha_060_dtl_par : '" + str (item[4]) +"' , nacha_060_coll_btch_no : '" + str (item[5]) +"'  , ifw_eff_dt : '" + str (item[6]) +"' , nacha_060_coll_pt : '" + str (item[7]) +"'\
        })"" "
        session.run(Src2File2Cmd)
        
        
    #Relationship
    # #Create relation kde to stg
    Stg1ToSrc1RelCmd  =  "MATCH (A:SRC1_STG), (B:SRC1_DATA) where \
                        (  substring('0000',0,case size(A.acc_9_ctl1)  when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end)+ A.acc_9_ctl1 \
                            + substring('0000',0,CASE size(A.acc_9_ctl2)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + A.acc_9_ctl2 \
                            + substring('0000',0,CASE size(A.acc_9_ctl3)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + A.acc_9_ctl3 \
                            + substring('0000',0,CASE size(A.acc_9_ctl4)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + A.acc_9_ctl4 \
                            + substring('0000000000',0,CASE size(A.acc_9_acct) when 1 then 9   when 2 then 8  when 3 then 7  when 4 then 6 when 5 then 5   \
                            when 6 then 4  when 7 then 3  when 8 then 2  when 9 then 1   when 10 then 0 end	) + A.acc_9_acct \
                                + A.acc_9_ccyyddd + A.acc_9_rec_seq )  = ( \
              substring('0000',0,case size(B.acc_9_ctl1)  when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end)+ B.acc_9_ctl1 \
            + substring('0000',0,CASE size(B.acc_9_ctl2)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl2  \
            + substring('0000',0,CASE size(B.acc_9_ctl3)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl3 \
            + substring('0000',0,CASE size(B.acc_9_ctl4)   when 1 then 3   when 2 then 2  when 3 then 1  when 4 then 0   end) + B.acc_9_ctl4  \
            + substring('0000000000',0,CASE size(B.acc_9_acct) when 1 then 9   when 2 then 8  when 3 then 7  when 4 then 6 when 5 then 5  \
            when 6 then 4  when 7 then 3  when 8 then 2  when 9 then 1   when 10 then 0 end	) + B.acc_9_acct + B.acc_9_ccyyddd + B.acc_9_rec_seq  ) \
                                 CREATE (A) <-[r:Extr_from_Src1data1_to_stg1]- (B) RETURN A, B " 
    
    Stg2ToSrc2File1RelCmd  =  "MATCH (A:SRC2_STG1), (B:SRC2_DATA1) where A.nacha_050_coll_file_no = B.nacha_050_coll_file_no \
                                AND A.nacha_050_coll_btch_no = B.nacha_050_coll_btch_no \
                                    AND A.dl_as_of_dt = B.dl_as_of_dt \
                                CREATE (A) <-[r:Extr_from_Src2File1_to_src2st1]- (B) \
                                RETURN A, B ;"  
                                
    Stg2ToSrc2File2RelCmd  =  "MATCH (A:SRC2_STG2), (B:SRC2_DATA2) where A.nacha_060_coll_file_no = B.nacha_060_coll_file_no \
                                AND A.nacha_060_coll_btch_no = B.nacha_060_coll_btch_no \
                                    AND A.dl_as_of_dt = B.dl_as_of_dt \
                                CREATE (A) <-[r:Extr_from_Src2File2_to_src2stg2]- (B) \
                                RETURN A, B "  
                                 
    session.run(Stg1ToSrc1RelCmd)
    session.run(Stg2ToSrc2File1RelCmd)
    session.run(Stg2ToSrc2File2RelCmd)
    
    
fetch_data_from_neo4j()