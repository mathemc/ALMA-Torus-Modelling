import os
import ast
import shutil
from casatasks import uvcontsub, split, mstransform, concat, tclean

print('')
print('# ========================================= #')
print('  Starting CATs code (CASA Automated Tasks)  ')
print('                                             ')
print('             |\---/|                         ')
print('             | ,_, |                         ')
print('              \_`_/-..----.                  ')
print('           ___/ `     ,  + \                 ')
print('          (__.../   __\    |`.___.-;         ')
print('            (_,.../(_,.`__)/\.....+          ')
print('                                             ')
print('              LEAPS Program 2026             ')
print('           Matheus Machado Carneiro          ')
print('# ========================================= #')

input_files      = ['uid___A002_Xdd4cf3_X384e.ms.split.cal',
                    'uid___A002_Xdd4cf3_X3c99.ms.split.cal',
                    'uid___A002_Xdd4cf3_X44f9.ms.split.cal',
                    'uid___A002_Xdd63f1_X3d04.ms.split.cal',
                    'uid___A002_Xdd63f1_X42b1.ms.split.cal',
                    'uid___A002_Xdd63f1_X4800.ms.split.cal',
                    'uid___A002_Xdd7274_X2f2d.ms.split.cal'] 

field_id        = 'NGC_1068'
spws            = '24'
input_fitspec   = '24:10~800;1600~1900'
input_split     = '24:810~1590'
emission_line   = 'HCO32'

# mstransform parameters
timebin_val     = '30s'
chanbin_val     = 10

# concat parameters
dirtol_val      = '0.003arcsec'
freqtol_val     = '30MHz'

# tclean parameters
cell_size       = '0.003arcsec'
img_size        = [2048, 2048]
phasecenter_val = 'J2000 02h42m40.710s -00d00m47.945s'
robust_val      = 0.5
threshold_val   = '0.0mJy'

# EXCLUDE INTERMEDIATE FILES
# Altere para True caso queira deletar os arquivos .ms intermediários ao final
del_file = True 


# ==============================================================================
# ===== 2. RUNNING UVCONTSUB ===== #
# ==============================================================================
print('\n# =================================== #')
print('            Running UVCONTSUB          ')
print('# =================================== #')

contsub_files = []
for i, vis_file in enumerate(input_files, start=1):
    print(f"\n[ {i}/{len(input_files)} ] Processando contsub em: {vis_file}")
    contsub_name = f"{field_id}_obs{i}_{emission_line}_csub.ms"
    contsub_files.append(contsub_name)
    
    if os.path.exists(contsub_name):
        shutil.rmtree(contsub_name)
    
    uvcontsub(
        vis=vis_file, outputvis=contsub_name, field=field_id,
        spw=spws, fitspec=input_fitspec, fitorder=1
    )
print('\n>> UVCONTSUB completed!')


# ==============================================================================
# ===== 3. RUNNING SPLIT ===== #
# ==============================================================================
print('\n# =================================== #')
print('              Running SPLIT            ')
print('# =================================== #')

split_files = []
for i, contsub_file in enumerate(contsub_files, start=1):
    print(f"\n[ {i}/{len(contsub_files)} ] Recortando: {contsub_file}")
    split_name = f"{field_id}_obs{i}_{emission_line}_split_v1.ms"
    split_files.append(split_name)
    
    if os.path.exists(split_name):
        shutil.rmtree(split_name)
    
    split(
        vis=contsub_file, outputvis=split_name, field=field_id,
        spw=input_split, datacolumn='data'
    )
print('\n>> SPLIT completed!')


# ==============================================================================
# ===== 4. RUNNING MSTRANSFORM ===== #
# ==============================================================================
print('\n# =================================== #')
print('           Running MSTRANSFORM         ')
print('# =================================== #')

mst_files = []
for i, split_file in enumerate(split_files, start=1):
    print(f"\n[ {i}/{len(split_files)} ] Aplicando mstransform em: {split_file}")
    mst_name = f"{field_id}_obs{i}_{emission_line}_mst_v1.ms"
    mst_files.append(mst_name)
    
    if os.path.exists(mst_name):
        shutil.rmtree(mst_name)
    
    mstransform(
        vis=split_file, outputvis=mst_name, datacolumn='data',
        field='', spw='0', timeaverage=True, timebin=timebin_val,
        chanaverage=True, chanbin=int(chanbin_val)
    )
print('\n>> MSTRANSFORM completed!')


# ==============================================================================
# ===== 5. RUNNING CONCAT ===== #
# ==============================================================================
print('\n# =================================== #')
print('             Running CONCAT            ')
print('# =================================== #')

concat_name = f"{field_id}_{emission_line}_concat.ms"

if os.path.exists(concat_name):
    shutil.rmtree(concat_name)

print(f"--> Gerando arquivo unificado em: {concat_name}")
concat(
    vis=mst_files, 
    concatvis=concat_name, 
    dirtol=dirtol_val, 
    freqtol=freqtol_val
)
print('\n>> CONCAT completed!')


# ==============================================================================
# ===== 6. RUNNING TCLEAN ===== #
# ==============================================================================
print('\n# =================================== #')
print('              Running TCLEAN           ')
print('# =================================== #')

image_prefix = f"{field_id}_{emission_line}_tcl_v1"

if os.path.exists(f"{image_prefix}.image"):
    print(f"--> Removendo imagens anteriores com o prefixo: {image_prefix}")
    os.system(f"rm -rf {image_prefix}.*")

print(f"--> Iniciando tclean usando o arquivo concatenado: {concat_name}")
tclean(
    vis=concat_name, 
    imagename=image_prefix,
    field='0', 
    specmode='cube',
    deconvolver='multiscale',
    scales=[0, 5, 10, 15, 30],
    gridder='standard',
    imsize=img_size, 
    cell=[cell_size], 
    weighting='briggs',
    phasecenter=phasecenter_val,
    robust=float(robust_val), 
    niter=1000000,
    nsigma=1.0,
    threshold=threshold_val,
    interactive=True 
)


# ==============================================================================
# ===== 7. CLEANUP INTERMEDIATE FILES ===== #
# ==============================================================================
if del_file:
    print('\n# =================================== #')
    print('   Cleaning up intermediate MS files   ')
    print('# =================================== #')
    
    # Agrupa todas as listas de MSs criados no processo
    all_intermediates = contsub_files + split_files + mst_files + [concat_name]
    
    removed_count = 0
    for ms_path in all_intermediates:
        if os.path.exists(ms_path):
            print(f"--> Removendo: {ms_path}")
            shutil.rmtree(ms_path)
            removed_count += 1
            
    print(f"\n>> Limpeza concluída: {removed_count} arquivos/diretórios MS removidos.")
else:
    print("\n>> Flag 'del_file' é False. Todos os arquivos MS intermediários foram mantidos.")

print('\n# ================================================== #')
print('  CAT CODE FINALIZADO COM SUCESSO! CUBOS GERADOS.   ')
print('# ================================================== #\n')
