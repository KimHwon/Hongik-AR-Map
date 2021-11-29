using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

using System;
using System.Text;
using System.Net.Sockets;

public class Destination : MonoBehaviour
{
    private static Destination instance = null;
    public Boolean isInputFilled = false;

    public InputField destination;
    Socket data_sock = Loading.Instance.GetDatatSocket();

    Notice notice;

    enum DataFormat : byte
    {
        EMPTY = 0x00,
        TEXT = 0x01,
        SENSOR = 0x02,
        DEST = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    public static Destination Instance
    {
        get
        {
            if (null == instance)
            {
                return null;
            }
            return instance;
        }
    }

    public void Navigate()
    {
        isInputFilled = true;

        byte[] msg = null;
        Boolean wrong = false;

        switch(destination.text)
        {
            case "T동":
                msg = Encoding.UTF8.GetBytes("T");
                break;
            case "S동":
                msg = Encoding.UTF8.GetBytes("S");
                break;
            case "Z1동":
                msg = Encoding.UTF8.GetBytes("1");
                break;
            case "Z2동":
                msg = Encoding.UTF8.GetBytes("2");
                break;
            case "2기숙사":
                msg = Encoding.UTF8.GetBytes("D");
                break;
            default:
                wrong = true;
                notice.SetNotice("잘못된 입력입니다. 다시 입력하세요.");
                break;
        }

        if (!wrong)
        {
            int i;
            buffer[0] = (byte)DataFormat.DEST;
            for (i = 0; i < Math.Min(buffer.Length - 2, msg.Length); i++)
                buffer[i + 1] = msg[i];
            buffer[i + 1] = ETX;

            data_sock.Send(buffer, 1024, SocketFlags.None);
        }
    }

    void Awake()
    {
        notice = FindObjectOfType<Notice>();

        if (null == instance)
        {
            instance = this;
            DontDestroyOnLoad(this.gameObject);
        }
        else
        {
            Destroy(this.gameObject);
        }
    }

    public Boolean GetIsInputFilled()
    {
        return isInputFilled;
    }
}
