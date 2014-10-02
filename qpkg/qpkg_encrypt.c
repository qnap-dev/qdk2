#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define BOOL                    int
#define TRUE                    1
#define FALSE                   0

// Common Error Code Definition
#define SUCCESS                 0   // function returns successfully
#define ERROR_FAIL              -1  // generic failure code

#define    BUF_SIZE             257

#define QNAPFLAG_ENCRYPT_KEY    3589
#define QNAPFLAG_FIELD_LEN      10
#define QNAPFLAG_MAX_LEN        100
#define QNAPFLAG_NAME_LEN       20

#define QPKGFLAG                "QNAPQPKG"
#define QFIXFLAG                "QNAPQFIX"

typedef struct QPKGFLAG_INFO {
    char model[BUF_SIZE];
    char name[BUF_SIZE];
    char version[BUF_SIZE];
    char flag[BUF_SIZE];
    char encrypt[BUF_SIZE];
    char auth_encrypt[BUF_SIZE];
    char fw_version[BUF_SIZE];
    char tmp[BUF_SIZE];
} QPKGFLAG_INFO;

/*************************************************
Function: Get_Str_By_Offset
Description:
get a string from offset of filename
Return values:
ERROR_FAIL/SUCCESS
Author: KenChen 2008/03/27
 **************************************************/
int Get_Str_By_Offset(char *filename, off_t offset, int length, char *str)
{
    char buf[BUF_SIZE + 1];
    int fd;
    unsigned int len;

    len = (length > BUF_SIZE) ? BUF_SIZE : length;

    if ((fd = open(filename, O_RDONLY)) < 0) {
        return ERROR_FAIL;
    }
    else {

        if (offset >= 0)
            lseek(fd, offset, SEEK_SET);
        else
            lseek(fd, offset, SEEK_END);
        read(fd, buf, len);
        close(fd);
        buf[len] = '\0';
        strcpy(str, buf);
    }
    return SUCCESS;
}

/*************************************************
Function: Is_QNAPFlag_Exist
Description:
Check QNAPFLAG(QPKGFLAG/QFIXFLAG)
Return values:
TRUE/FALSE
Author: KenChen 2008/03/27
 **************************************************/
BOOL Is_QNAPFlag_Exist(char *filename, char *flag)
{
    char buf[BUF_SIZE + 1];
    int ret;
    int len;
    off_t loc;

    if (flag == NULL) return FALSE;
    len = strlen(flag);
    loc = -1 * QNAPFLAG_FIELD_LEN;

    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret == SUCCESS && !strncmp(flag, buf, len))
        return TRUE;

    return FALSE;
}

/*************************************************
Function: Get_QNAPFlag_File_Info
Description:
get QNAPFLAG info embedded in the file.
Return values:
SUCCESS/ERROR_FAIL
Author: KenChen 2008/03/28
 **************************************************/
int Get_QNAPFlag_File_Info(char *filename, QPKGFLAG_INFO *qinfo)
{
    char buf[BUF_SIZE];
    int ret;
    off_t loc;

    loc = -1 * QNAPFLAG_MAX_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->model, buf, sizeof(buf));

    loc = -1 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->flag, buf, sizeof(buf));

    loc = -2 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->version, buf, sizeof(buf));

    loc = -4 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_NAME_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->name, buf, sizeof(buf));

    loc = -5 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->fw_version, buf, sizeof(buf));

    loc = -6 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->encrypt, buf, sizeof(buf));

    loc = -7 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->auth_encrypt, buf, sizeof(buf));

    loc = -8 * QNAPFLAG_FIELD_LEN;
    ret = Get_Str_By_Offset(filename, loc, QNAPFLAG_FIELD_LEN, buf);
    if (ret != SUCCESS)
        return ERROR_FAIL;
    else
        strncpy(qinfo->tmp, buf, sizeof(buf));

    return ret;
}

/*************************************************
Function: Get_QPKG_Encrypt_String
Description:
get QPKG Encrypt String (len=10)
Return values:
ERROR_FAIL/SUCCESS
Author: KenChen 2008/04/10
 **************************************************/
int Get_QPKG_Encrypt_String(char *filename, char *en_str)
{
    unsigned long long en_longlong;
    char buf[BUF_SIZE];
    struct stat mystatus;
    QPKGFLAG_INFO qinfo;

    if (lstat(filename, &mystatus) != 0)
        return ERROR_FAIL;
    else if (!S_ISREG(mystatus.st_mode))
        return ERROR_FAIL;

    if (!Is_QNAPFlag_Exist(filename, QPKGFLAG) && !Is_QNAPFlag_Exist(filename, QFIXFLAG))
        return ERROR_FAIL;
    if (Get_QNAPFlag_File_Info(filename, &qinfo) != SUCCESS)
        return ERROR_FAIL;

    en_longlong = (unsigned long long)mystatus.st_size * QNAPFLAG_ENCRYPT_KEY + 1000000000;
    sprintf(buf, "%llu", en_longlong);

    buf[10] = '\0';
    strcpy(en_str, buf);

    return SUCCESS;
}

/*************************************************
Function: Set_QPKG_Encrypt
Description:
set encryption string into QPKG file
Return values:
ERROR_FAIL/SUCCESS
Author: KenChen 2008/04/10
 **************************************************/
int Set_QPKG_Encrypt(char *filename)
{
    char en_str[10 + 1];
    FILE *fpt;
    int i;

    if (Get_QPKG_Encrypt_String(filename, en_str) != SUCCESS)
        return ERROR_FAIL;

    if ((fpt = fopen(filename, "rb+")) == NULL)
        return ERROR_FAIL;

    fseek(fpt, -6 * QNAPFLAG_FIELD_LEN, SEEK_END);
    for (i = 0; i < 10; i++)
        fprintf(fpt, "%c", en_str[i]);

    fclose(fpt);

    return SUCCESS;
}

void usage()
{
    printf("usage: qpkg_encrypt <filename>\n");
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        usage();
        return 1;
    }
    else if (access(argv[1], F_OK) == -1) {
        perror(argv[1]);
        return 2;
    }
    else if (Set_QPKG_Encrypt(argv[1]) != SUCCESS) {
        fprintf(stderr, "%s: Invalid QPKG format\n", argv[1]);
        return 3;
    }

    return 0;
}
