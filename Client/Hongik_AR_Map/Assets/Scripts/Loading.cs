using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

using System;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.IO;
using System.Text;

public class Loading : MonoBehaviour
{
    private static Loading instance = null; // for singleton

    Boolean connectionRefused = false;

    Socket image_sock = null;
    Socket data_sock = null;

    string IP = "172.30.1.59";

    GameObject loadingSpinner = null;
    GameObject loadingText = null;

    enum DataFormat : byte
    {
        EMPTY = 0x00,
        TEXT = 0x01,
        SENSOR = 0x02,
        DEST = 0x03
    };
    const byte ETX = 0x03;

    byte[] buffer = new byte[1024];

    public static Loading Instance
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

    void Start()
    {
        loadingSpinner = GameObject.Find("Image");
        loadingText = GameObject.Find("Text");

        // Try 10 sec(20 times) to connect
        StartCoroutine("ConnectToServer");

    }

    IEnumerator ConnectToServer()
    {
        WaitForSeconds wait = new WaitForSeconds(0.5f);

        string configPath = Application.persistentDataPath + "/config.txt";
        if (File.Exists(configPath))
        {
            StreamReader reader = new StreamReader(configPath);
            string data = reader.ReadToEnd();
            IP = data;
            reader.Close();
        }
        else
        {
            StreamWriter writer = new StreamWriter(configPath);
            string data = IP;
            writer.Write(data);
            writer.Close();
        }

        for (int i = 1; i <= 20; i++)
        {
            try
            {
                image_sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                IPEndPoint ep1 = new IPEndPoint(IPAddress.Parse(IP), 50020);
                image_sock.Connect(ep1);

                data_sock = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
                IPEndPoint ep2 = new IPEndPoint(IPAddress.Parse(IP), 50021);
                data_sock.Connect(ep2);

                loadingSpinner.SetActive(false);
                loadingText.SetActive(false);

                SceneManager.LoadScene("Home");
                yield break;
            }
            catch (Exception e)
            {
                Debug.Log(e);
                if (i == 20)
                {
                    loadingSpinner.SetActive(false);
                    loadingText.SetActive(false);

                    SceneManager.LoadScene("Failed");
                    yield break;
                }
            }

            yield return wait; // Pause the loop for 0.5 seconds
        }

    }

    void Awake()
    {
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

    // singleton
    public Socket GetDatatSocket()
    {
        return data_sock;
    }

    public Socket GetImageSocket()
    {
        return image_sock;
    }

    public string GetIP()
    {
        return IP;
    }
}
