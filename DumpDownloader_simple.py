#!/usr/bin/python3
# -*- coding: utf-8 -*-
import urllib.request
import argparse
import os
import time
import sys

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=''''Downloads all wiki-Dumps, except the ones already stored in the given directory(does not 
        include subdirectories). You may want to manually delete/move them if you want the program to download them 
        too.''',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-d', '--io_dir',
                        help='The input & output directory name, where (possibly) existing dumps are and downloaded '
                             'ones should be stored. Defaults to current directory.',
                        default='./', type=str, dest='io_dir')
    parser.add_argument("-v", "--verbosity", action="count", default=0, dest='verbosity_level')
    parser.add_argument('-m', '--multistream', default=False)
    args = parser.parse_args()

    # check io_dir
    current_dir_path = os.path.dirname(os.path.realpath(__file__))
    complete_dir_path = os.path.join(current_dir_path, args.io_dir)
    if not os.path.exists(args.io_dir):  # make io_dir
        os.mkdir(complete_dir_path)

    # copied from https://meta.wikimedia.org/wiki/List_of_Wikipedias (only exchanged "-" with "_" and used "be_x_old"
    # instead of "be_tarask");   if you need to update this: copy the table from the link and paste it to Excel to
    # extract the language-codes easily
    language_codes = '''en,ceb,sv,de,fr,nl,ru,it,es,pl,war,vi,ja,zh,pt,ar,uk,fa,sr,ca,no,id,ko,fi,hu,sh,cs,ro,eu,tr,
    ms,eo,hy,bg,da,he,ce,sk,zh_min_nan,kk,min,hr,et,lt,be,el,sl,gl,azb,nn,az,simple,ur,th,hi,ka,uz,la,ta,vo,cy,mk,
    ast,tg,lv,mg,tt,oc,af,bs,ky,sq,tl,zh_yue,bn,new,te,be_x_old,br,ml,pms,su,lb,ht,jv,nds,sco,mr,sw,ga,ba,is,pnb,my,
    fy,cv,lmo,an,ne,yo,pa,bar,io,gu,als,ku,scn,bpy,kn,ckb,ia,wuu,qu,arz,mn,bat_smg,wa,si,or,yi,am,gd,cdo,nap,bug,mai,
    hsb,ilo,map_bms,fo,xmf,mzn,li,vec,sd,eml,sah,os,sa,diq,ps,mrj,mhr,zh_classical,hif,nv,roa_tara,ace,bcl,frr,hak,
    szl,pam,nso,km,se,hyw,rue,mi,nah,vls,bh,nds_nl,crh,gan,vep,sc,ab,as,bo,glk,myv,co,tk,fiu_vro,so,lrc,kv,csb,shn,
    gv,sn,udm,zea,ay,ie,pcd,nrm,kab,ug,stq,lez,kw,ha,lad,mwl,haw,gom,gn,rm,lij,lfn,lo,koi,mt,frp,fur,dsb,ext,ang,ln,
    dty,olo,cbk_zam,dv,ksh,bjn,gag,pi,pfl,pag,av,bxr,gor,xal,krc,za,pap,kaa,pdc,tyv,rw,to,kl,nov,arc,jam,kbp,kbd,tpi,
    tet,ig,ki,zu,wo,na,sat,jbo,roa_rup,lbe,bi,ty,mdf,kg,lg,tcy,srn,inh,xh,atj,ltg,chr,sm,pih,om,tn,ak,cu,ts,tw,rmy,
    bm,st,chy,rn,got,tum,ny,ss,ch,pnt,fj,iu,ady,ve,ee,ks,ik,sg,ff,dz,ti,din,cr,ng,cho,kj,mh,ho,ii,aa,mus,hz,
    kr'''.split(',')

    # remove already downloaded files from download-list (=>manually delete files where you want newer dumps to be
    # downloaded!)
    removed_languages = 0
    for lang in language_codes:
        for root, directories, f_names in os.walk(args.io_dir):
            for filename in f_names:
                if filename.startswith(lang + "wiki") and filename.endswith(".bz2"):
                    language_codes.remove(lang)
                    removed_languages += 1
                    if args.verbosity_level > 0:
                        print("Skipping language " + lang + ", since " + filename + " already exists!")
            break  # don't search in subdirectories

    # download
    num_of_downloads = 0
    max_num_of_downloads = len(language_codes)  # change this if you want only want to download the x biggest dumps
    print("Downloading the maximum allowed " + str(max_num_of_downloads) + " dumps of " + str(
        len(language_codes)) + " dumps not stored on disc.")
    if removed_languages > 0:
        print("An additional " + str(removed_languages) +
              "dumps are already on disc and thus won't be re-downloaded/updated. You may want to manually delete "
              "those to enable the download!")
    for lang in language_codes:
        # not downloading the multistream-file, since wikiFilter.py does not support multistream-files
        if args.multistream:
            dump_suffix = "wiki-latest-pages-articles-multistream.xml.bz2"
        else:
            dump_suffix = "wiki-latest-pages-articles.xml.bz2"
        url = "https://dumps.wikimedia.org/" + lang + "wiki/latest/" + lang + dump_suffix
        o_filename = lang + dump_suffix
        try:
            t_start = time.perf_counter()
            (filename, headers) = urllib.request.urlretrieve(url, os.path.join(complete_dir_path, o_filename))
            print("Downloaded language: " + lang + " (" + str(os.stat(filename).st_size) + " bytes) in " + str(
                (time.perf_counter() - t_start) / 60) + " minutes.")
            sys.stdout.flush()  # unbuffered output => no need to manually call "python -u"
            num_of_downloads += 1
        except Exception as e:
            print("Error with lang: " + lang)
            print(e)
        if num_of_downloads > max_num_of_downloads:
            print(str(
                max_num_of_downloads) +
                  " files downloaded. Stopping download because the maximum allowed number has been reached!")
            break

    print("Downloaded " + str(num_of_downloads) + " files, while skipping " + str(
        removed_languages) +
          " already existing files(those might be outdated, so consider deleting them & running this program again!).")

# todo: check if download date of already existing file(s) < date of newest dump consider using a mirror for lower
#  load on the servers check MD5-checksums & re-download (only re-download once!) name the files according to the
#  date the dumps where created - helpful for documentation purposes, since the download link depends on this
