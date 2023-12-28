#include <stdio.h>
#include <string.h>
#include <dirent.h>

char *read_single_file(char *dir, char *f_name)
{
    // load file name
    char df_name[256];
    strcpy(df_name, "/home/iwmain/Documents/diaries/");
    strcat(df_name, dir);
    strcat(df_name, f_name);
    // Read the content
    static char ans[8192];
    memset(ans, 0, sizeof(ans));
    FILE *fp;
    fp = fopen(df_name, "r");
    if (fp == NULL) {
        printf("Failed to open file %s\n", df_name);
        return ans;
        // exit(-1);
    }
    char s[100];
    while (1)
    {
        fscanf(fp, "%99s", &s);
        strcat(ans, s);
        if (feof(fp))
            break;
    }
    return ans;
}

int main()
/*Write all the diaries and comments into a single file*/
{

    DIR *d;
    struct dirent *dir;
    d = opendir("/home/iwmain/Documents/diaries/"); // Opens the current directory
    FILE *fp;
    fp = fopen("test.txt", "w");

    if (d)
    {
        while ((dir = readdir(d)) != NULL)
        {
            fprintf(fp, "%s\n", read_single_file(dir->d_name, "/diary.txt"));
            fprintf(fp, "%s\n\n", read_single_file(dir->d_name, "/comment.txt"));
        }
        closedir(d);
    }
    fclose(fp);

    return 0;
}